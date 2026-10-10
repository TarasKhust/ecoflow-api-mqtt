"""Regression coverage for Stream MQTT watchdog backoff (issue #75).

PV-only Stream units (e.g. microinverters) go legitimately quiet overnight.
The watchdog must still retry the first silence promptly, but consecutive
silent reconnects must back off to a bounded interval instead of holding a
~2 minute reconnect cycle all night. Genuinely new MQTT information resets
the backoff; identical replays do not. Non-Stream behavior is unchanged.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

from custom_components.ecoflow_api.const import (
    DEVICE_TYPE_DELTA_PRO_3,
    DEVICE_TYPE_STREAM_MICRO_INVERTER,
)
from custom_components.ecoflow_api.hybrid_coordinator import (
    MQTT_SILENCE_THRESHOLD,
    MQTT_SILENCE_THRESHOLD_STREAM,
    MQTT_WATCHDOG_MAX_THRESHOLD_STREAM,
    EcoFlowHybridCoordinator,
)


class FakeLoop:
    """Minimal event-loop stand-in: record scheduling, never execute."""

    def __init__(self) -> None:
        self.scheduled: list[tuple[float, Any]] = []
        self.posted: list[Any] = []

    def is_running(self) -> bool:
        return True

    def is_closed(self) -> bool:
        return False

    def call_later(self, delay: float, callback: Any) -> SimpleNamespace:
        self.scheduled.append((delay, callback))
        return SimpleNamespace(cancel=lambda: None)

    def call_soon_threadsafe(self, callback: Any) -> None:
        self.posted.append(callback)


class FakeMqttClient:
    """Record watchdog disconnects without touching the network."""

    def __init__(self) -> None:
        self.disconnects = 0

    async def async_disconnect(self) -> None:
        self.disconnects += 1


def make_watchdog_coordinator(
    device_type: str, clock: dict[str, float]
) -> tuple[EcoFlowHybridCoordinator, FakeMqttClient, list[int]]:
    """Build a hybrid coordinator with stubbed HA/transport boundaries."""
    loop = FakeLoop()
    coordinator = object.__new__(EcoFlowHybridCoordinator)
    coordinator.device_sn = "TESTDEVICE01"
    coordinator.device_type = device_type
    coordinator.hass = SimpleNamespace(loop=loop)
    coordinator._mqtt_client = FakeMqttClient()
    coordinator._mqtt_connected = True
    coordinator._mqtt_silence_threshold = (
        MQTT_SILENCE_THRESHOLD_STREAM
        if coordinator.is_stream_device
        else MQTT_SILENCE_THRESHOLD
    )
    coordinator._mqtt_silent_reconnects = 0
    coordinator._last_mqtt_message_time = clock["now"]
    coordinator._mqtt_watchdog_timer = None
    coordinator._shutting_down = False
    coordinator._mqtt_data = {}
    coordinator._last_data = {}
    coordinator._diagnostic_mode = False

    setup_calls: list[int] = []

    async def fake_setup_mqtt() -> None:
        """Emulate a successful reconnect: connected, silence clock restarts."""
        setup_calls.append(1)
        coordinator._mqtt_connected = True
        coordinator._last_mqtt_message_time = clock["now"]

    coordinator._async_setup_mqtt = fake_setup_mqtt  # type: ignore[method-assign]
    return coordinator, coordinator._mqtt_client, setup_calls


async def test_stream_first_silence_retries_promptly(monkeypatch) -> None:
    """The first 90 s+ silence on a Stream device must reconnect immediately."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, setup_calls = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )
    coordinator._last_mqtt_message_time = clock["now"] - 120

    await coordinator._mqtt_watchdog_tick()

    assert mqtt.disconnects == 1
    assert setup_calls == [1]
    assert coordinator._mqtt_silent_reconnects == 1


async def test_stream_repeat_silence_backs_off(monkeypatch) -> None:
    """After one silent reconnect the threshold grows by one backoff step."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, setup_calls = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )
    coordinator._last_mqtt_message_time = clock["now"] - 120
    await coordinator._mqtt_watchdog_tick()
    assert coordinator._mqtt_silent_reconnects == 1

    # 120 s of new silence is below the backed-off 150 s threshold: no retry.
    clock["now"] += 120
    await coordinator._mqtt_watchdog_tick()
    assert mqtt.disconnects == 1
    assert setup_calls == [1]
    assert coordinator._mqtt_silent_reconnects == 1

    # At 180 s (>= 90 + 60) the second retry fires.
    clock["now"] += 60
    await coordinator._mqtt_watchdog_tick()
    assert mqtt.disconnects == 2
    assert setup_calls == [1, 1]
    assert coordinator._mqtt_silent_reconnects == 2


async def test_stream_backoff_bounded_at_one_hour(monkeypatch) -> None:
    """The effective threshold never exceeds the hourly bound."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, setup_calls = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )
    coordinator._mqtt_silent_reconnects = 1_000

    coordinator._last_mqtt_message_time = clock["now"] - (
        MQTT_WATCHDOG_MAX_THRESHOLD_STREAM - 1
    )
    await coordinator._mqtt_watchdog_tick()
    assert mqtt.disconnects == 0
    assert setup_calls == []

    coordinator._last_mqtt_message_time = (
        clock["now"] - MQTT_WATCHDOG_MAX_THRESHOLD_STREAM
    )
    await coordinator._mqtt_watchdog_tick()
    assert mqtt.disconnects == 1
    assert setup_calls == [1]


async def test_stream_backoff_overnight_reconnects_bounded(monkeypatch) -> None:
    """A 13 h quiet night stays in the dozens of reconnects, not hundreds."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, _ = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )

    # Simulate the 60 s watchdog cadence across a 13 h night with zero traffic.
    night_end = clock["now"] + 13 * 3600
    while clock["now"] < night_end:
        clock["now"] += 60
        await coordinator._mqtt_watchdog_tick()

    assert mqtt.disconnects < 60
    # And the steady state is hourly: last interval reaches the bound.
    assert coordinator._mqtt_silent_reconnects == mqtt.disconnects


async def test_new_information_resets_backoff(monkeypatch) -> None:
    """A message with new field values clears the backoff for fast retry."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, _, _ = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )
    coordinator._mqtt_silent_reconnects = 3
    coordinator._last_mqtt_message_time = clock["now"] - 500

    coordinator._handle_mqtt_message({"someField": 1})

    assert coordinator._mqtt_silent_reconnects == 0
    assert coordinator._last_mqtt_message_time == clock["now"]

    # Next stall is judged against the base 90 s threshold again.
    clock["now"] += MQTT_SILENCE_THRESHOLD_STREAM + 1
    await coordinator._mqtt_watchdog_tick()
    assert coordinator._mqtt_silent_reconnects == 1


async def test_identical_replay_does_not_reset_backoff(monkeypatch) -> None:
    """A duplicate snapshot (e.g. retained replay on reconnect) keeps backoff.

    The silence clock still restarts on any receipt, but the backoff built up
    while the unit was quiet must survive identical replays — otherwise a
    broker that re-delivers the last snapshot on every reconnect would hold
    the retry cycle at ~2 minutes all night.
    """
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, _ = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )
    coordinator._mqtt_data = {"someField": 1}
    coordinator._mqtt_silent_reconnects = 3
    coordinator._last_mqtt_message_time = clock["now"] - 500

    coordinator._handle_mqtt_message({"someField": 1})

    assert coordinator._mqtt_silent_reconnects == 3
    assert coordinator._last_mqtt_message_time == clock["now"]

    # Still backed off: 200 s of further silence stays below 90 + 3*60 = 270.
    clock["now"] += 200
    await coordinator._mqtt_watchdog_tick()
    assert mqtt.disconnects == 0
    assert coordinator._mqtt_silent_reconnects == 3


async def test_non_stream_threshold_unchanged_by_repeats(monkeypatch) -> None:
    """Non-Stream devices keep the fixed 180 s threshold on every cycle."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, setup_calls = make_watchdog_coordinator(
        DEVICE_TYPE_DELTA_PRO_3, clock
    )

    for _ in range(4):
        coordinator._last_mqtt_message_time = clock["now"] - (
            MQTT_SILENCE_THRESHOLD + 20
        )
        await coordinator._mqtt_watchdog_tick()

        # Below-threshold tick after each reconnect must stay quiet.
        clock["now"] += MQTT_SILENCE_THRESHOLD - 60
        before = mqtt.disconnects
        await coordinator._mqtt_watchdog_tick()
        assert mqtt.disconnects == before

    assert mqtt.disconnects == 4
    assert len(setup_calls) == 4


async def test_tick_noop_guards(monkeypatch) -> None:
    """Disconnected, never-seen, or shutting-down coordinators never retry."""
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator, mqtt, setup_calls = make_watchdog_coordinator(
        DEVICE_TYPE_STREAM_MICRO_INVERTER, clock
    )

    coordinator._mqtt_connected = False
    coordinator._last_mqtt_message_time = clock["now"] - 10_000
    await coordinator._mqtt_watchdog_tick()

    coordinator._mqtt_connected = True
    coordinator._last_mqtt_message_time = None
    await coordinator._mqtt_watchdog_tick()

    assert mqtt.disconnects == 0
    assert setup_calls == []
    assert coordinator._mqtt_silent_reconnects == 0
    # Quiet ticks still reschedule the watchdog for the next interval.
    assert len(coordinator.hass.loop.scheduled) == 2
