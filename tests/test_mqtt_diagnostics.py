"""Per-device MQTT diagnostics for issue #84.

Two diagnostic sensors backed by the hybrid coordinator:
- "Last MQTT message received" (TIMESTAMP): separately initialized None,
  updated only on device quota telemetry, timezone-aware UTC.
- "Consecutive silent watchdog reconnects": exposes the existing
  ``_mqtt_silent_reconnects`` counter with unchanged increment/reset/backoff.

Watchdog semantics are preserved: the legacy ``_last_mqtt_message_time``
baseline still restarts on every receipt (including unknown-topic echoes),
backoff still resets only on new/changed data, and unknown-topic echoes keep
their legacy merge processing while never advancing the new received
timestamp (via an ``is_telemetry`` flag, not a routing change).
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

from custom_components.ecoflow_api import sensor as sensor_module
from custom_components.ecoflow_api.const import (
    DEVICE_TYPE_DELTA_PRO_3,
    DEVICE_TYPE_STREAM_MICRO_INVERTER,
    DOMAIN,
)
from custom_components.ecoflow_api.coordinator import EcoFlowDataCoordinator
from custom_components.ecoflow_api.hybrid_coordinator import (
    MQTT_SILENCE_THRESHOLD,
    EcoFlowHybridCoordinator,
)
from custom_components.ecoflow_api.mqtt_client import EcoFlowMQTTClient, mqtt
from custom_components.ecoflow_api.sensor import (
    EcoFlowLastMqttMessageSensor,
    EcoFlowSilentReconnectsSensor,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory


class FakeLoop:
    """Minimal loop: record scheduling, run threadsafe callbacks inline."""

    def __init__(self) -> None:
        self.scheduled: list = []
        self.updated: list = []

    def is_running(self) -> bool:
        return True

    def is_closed(self) -> bool:
        return False

    def call_later(self, delay: float, callback: Any) -> SimpleNamespace:
        self.scheduled.append((delay, callback))
        return SimpleNamespace(cancel=lambda: None)

    def call_soon_threadsafe(self, callback: Any, *args: Any) -> None:
        callback(*args) if args else callback()


class FakeMqttTransportClient:
    """Record watchdog disconnects without touching the network."""

    def __init__(self) -> None:
        self.disconnects = 0

    async def async_disconnect(self) -> None:
        self.disconnects += 1


def make_diag_coordinator(
    device_type: str = DEVICE_TYPE_DELTA_PRO_3,
) -> EcoFlowHybridCoordinator:
    """Build a hybrid coordinator stub with real diagnostic methods."""
    coordinator = object.__new__(EcoFlowHybridCoordinator)
    coordinator.device_sn = "TESTDEVICE01"
    coordinator.device_type = device_type
    coordinator.hass = SimpleNamespace(loop=FakeLoop())
    coordinator._mqtt_client = FakeMqttTransportClient()
    coordinator._mqtt_connected = True
    coordinator._mqtt_reconnect_count = 0
    coordinator._use_mqtt = False
    coordinator._logged_rest_success = False
    coordinator.update_interval_seconds = 15
    coordinator._last_rest_update = None
    coordinator._mqtt_silence_threshold = MQTT_SILENCE_THRESHOLD
    coordinator._mqtt_silent_reconnects = 0
    coordinator._last_mqtt_message_time = None
    coordinator._last_mqtt_telemetry_time = None
    coordinator._mqtt_diagnostic_listeners = set()
    coordinator._mqtt_data = {}
    coordinator._last_data = {}
    coordinator._diagnostic_mode = False
    coordinator._shutting_down = False
    coordinator._mqtt_watchdog_timer = None
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator._merged_updates = []

    def fake_set_updated_data(data: dict) -> None:
        coordinator._merged_updates.append(data)
        coordinator.data = data

    coordinator.async_set_updated_data = fake_set_updated_data  # type: ignore[method-assign]

    async def fake_setup_mqtt() -> None:
        """Emulate reconnect: baseline restarts, telemetry untouched."""
        coordinator._mqtt_connected = True
        coordinator._last_mqtt_message_time = time.time()

    coordinator._async_setup_mqtt = fake_setup_mqtt  # type: ignore[method-assign]
    return coordinator


def make_entry(entry_id: str = "entry84") -> SimpleNamespace:
    return SimpleNamespace(entry_id=entry_id, data={"device_type": "TEST84"})


# --- initialization ------------------------------------------------------

async def test_telemetry_timestamp_initially_none() -> None:
    coordinator = make_diag_coordinator()
    assert coordinator.last_mqtt_message_received is None
    assert coordinator._last_mqtt_telemetry_time is None

    sensor = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    assert sensor.native_value is None
    assert sensor.available is True
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    assert sensor.name == "Last MQTT message received"
    assert sensor.unique_id == "entry84_last_mqtt_message_received"
    assert sensor.translation_key == "last_mqtt_message_received"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


async def test_counter_initially_zero_and_available() -> None:
    coordinator = make_diag_coordinator()
    assert coordinator.mqtt_silent_reconnects == 0
    sensor = EcoFlowSilentReconnectsSensor(coordinator, make_entry())
    assert sensor.native_value == 0
    assert sensor.available is True
    assert sensor.name == "Consecutive silent watchdog reconnects"
    assert sensor.unique_id == "entry84_consecutive_silent_watchdog_reconnects"
    assert sensor.translation_key == "consecutive_silent_watchdog_reconnects"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


# --- telemetry receipts ---------------------------------------------------

async def test_quota_telemetry_sets_aware_utc_timestamp() -> None:
    coordinator = make_diag_coordinator()
    coordinator._handle_mqtt_message({"soc": 42})
    received = coordinator.last_mqtt_message_received
    assert isinstance(received, datetime)
    assert received.tzinfo is not None
    assert received.utcoffset() == timezone.utc.utcoffset(None)
    assert EcoFlowLastMqttMessageSensor(coordinator, make_entry()).native_value is received


async def test_identical_payload_still_advances_timestamp() -> None:
    """A broker replay counts: identical live reading vs snapshot are indistinguishable."""
    coordinator = make_diag_coordinator()
    coordinator._handle_mqtt_message({"soc": 42})
    first = coordinator.last_mqtt_message_received
    coordinator._handle_mqtt_message({"soc": 42})
    second = coordinator.last_mqtt_message_received
    assert first is not None and second is not None
    assert second >= first


async def test_identical_replay_keeps_silent_backoff() -> None:
    """Backoff behavior unchanged: identical replay does not reset the count."""
    coordinator = make_diag_coordinator()
    coordinator._mqtt_data = {"soc": 42}
    coordinator._mqtt_silent_reconnects = 3
    coordinator._handle_mqtt_message({"soc": 42})
    assert coordinator.mqtt_silent_reconnects == 3
    # But the received timestamp still advanced (replay counts as receipt).
    assert coordinator.last_mqtt_message_received is not None


async def test_new_data_resets_silent_backoff() -> None:
    coordinator = make_diag_coordinator()
    coordinator._mqtt_silent_reconnects = 3
    coordinator._handle_mqtt_message({"soc": 43})
    assert coordinator.mqtt_silent_reconnects == 0


# --- non-telemetry sources never advance ----------------------------------

async def test_unknown_topic_echo_preserves_legacy_but_not_timestamp() -> None:
    """Unknown echoes keep merge/baseline processing, never the new timestamp."""
    coordinator = make_diag_coordinator()
    coordinator._handle_mqtt_message({"soc": 1}, is_telemetry=False)
    assert coordinator.last_mqtt_message_received is None
    # Legacy behavior preserved: watchdog baseline restarted and data merged.
    assert coordinator._last_mqtt_message_time is not None
    assert coordinator._mqtt_data.get("soc") == 1


async def test_broker_status_flaps_do_not_advance_timestamp() -> None:
    coordinator = make_diag_coordinator()
    coordinator._mqtt_connected = False
    coordinator._handle_mqtt_status(True)  # initial connect
    assert coordinator.last_mqtt_message_received is None
    baseline = coordinator._last_mqtt_message_time
    assert baseline is not None
    coordinator._handle_mqtt_status(False)  # disconnect
    coordinator._handle_mqtt_status(True)  # reconnect
    assert coordinator.last_mqtt_message_received is None
    assert coordinator._last_mqtt_message_time is not None


async def test_rest_update_does_not_advance_timestamp(monkeypatch) -> None:
    """REST polling (success or failure) never advances the MQTT receipt clock."""
    coordinator = make_diag_coordinator()
    marker = datetime(2026, 1, 1, tzinfo=timezone.utc)
    coordinator._last_mqtt_telemetry_time = marker

    async def fake_quota(sn: str) -> dict:
        return {"soc": 55}

    coordinator.client = SimpleNamespace(get_device_quota=fake_quota)

    async def noop_wake() -> None:
        return None

    monkeypatch.setattr(coordinator, "_async_wake_device", noop_wake)

    data = await coordinator._async_update_data()
    assert data["soc"] == 55
    assert coordinator.last_mqtt_message_received is marker

    # REST failure path also leaves the timestamp alone.
    async def failing_quota(sn: str) -> dict:
        from custom_components.ecoflow_api.api import EcoFlowApiError

        raise EcoFlowApiError("boom")

    coordinator.client = SimpleNamespace(get_device_quota=failing_quota)
    coordinator._use_mqtt = False
    try:
        await coordinator._async_update_data()
    except Exception:
        pass
    assert coordinator.last_mqtt_message_received is marker


# --- mqtt_client routing / ACK / parsing -----------------------------------

def _msg(topic: str, payload: Any) -> SimpleNamespace:
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return SimpleNamespace(topic=topic, payload=raw)


async def test_quota_topics_parse_and_tag_telemetry() -> None:
    seen: list = []
    client = EcoFlowMQTTClient(
        username="u",
        password="p",
        device_sn="SN",
        certificate_account="ACC",
        on_message_callback=lambda payload, is_telemetry=True: seen.append(
            (payload, is_telemetry)
        ),
    )
    client._on_message(None, None, _msg("/open/ACC/SN/quota", {"params": {"soc": 7}}))
    client._on_message(None, None, _msg("/open/ACC/SN/quota", {"param": {"pv": 1}}))
    client._on_message(None, None, _msg("/open/ACC/SN/quota", {"soc": 9}))
    assert seen[0] == ({"soc": 7}, True)
    assert seen[1] == ({"20_1": {"pv": 1}}, True)
    assert seen[2] == ({"soc": 9}, True)


async def test_unknown_topic_tagged_non_telemetry() -> None:
    seen: list = []
    client = EcoFlowMQTTClient(
        username="u",
        password="p",
        device_sn="SN",
        certificate_account="ACC",
        on_message_callback=lambda payload, is_telemetry=True: seen.append(
            (payload, is_telemetry)
        ),
    )
    client._on_message(None, None, _msg("/open/ACC/SN/something-else", {"x": 1}))
    assert seen == [({"x": 1}, False)]


async def test_status_and_ack_never_count_as_telemetry() -> None:
    calls: list = []
    loop = asyncio.get_running_loop()
    client = EcoFlowMQTTClient(
        username="u",
        password="p",
        device_sn="SN",
        certificate_account="ACC",
        on_message_callback=lambda payload, is_telemetry=True: calls.append(payload),
        loop=loop,
    )
    client._on_message(
        None, None, _msg("/open/ACC/SN/status", {"params": {"status": 1}})
    )
    assert calls == []

    # set_reply resolves the matching command ACK and never emits telemetry.
    transport_calls: list = []

    class Transport:
        def publish(self, topic: str, payload: str, qos: int) -> SimpleNamespace:
            transport_calls.append(topic)
            return SimpleNamespace(rc=mqtt.MQTT_ERR_SUCCESS)

    client._connected = True
    client._client = Transport()
    task = asyncio.create_task(
        client.async_publish_command({"id": 77, "sn": "SN", "params": {}}, ack_timeout=2)
    )
    await asyncio.sleep(0)
    client._on_message(
        None,
        None,
        _msg("/open/ACC/SN/set_reply", {"id": 77, "data": {"result": 0}}),
    )
    assert await asyncio.wait_for(task, 2) is True
    assert calls == []


# --- counter / watchdog ----------------------------------------------------

async def test_watchdog_increment_notifies_even_when_reconnect_fails(
    monkeypatch,
) -> None:
    """Counter increments notify diagnostics even if the reconnect fails."""
    coordinator = make_diag_coordinator()
    coordinator._last_mqtt_message_time = time.time() - 10_000
    notified: list = []
    coordinator.async_add_mqtt_diagnostic_listener(lambda: notified.append(1))

    async def failing_setup() -> None:
        coordinator._mqtt_connected = False  # reconnect failed, count stays

    coordinator._async_setup_mqtt = failing_setup  # type: ignore[method-assign]
    monkeypatch.setattr(
        EcoFlowHybridCoordinator, "_async_setup_mqtt", failing_setup
    )
    await coordinator._mqtt_watchdog_tick()
    assert coordinator.mqtt_silent_reconnects == 1
    assert notified == [1]
    assert EcoFlowSilentReconnectsSensor(coordinator, make_entry()).native_value == 1


async def test_watchdog_backoff_growth_preserved(monkeypatch) -> None:
    """Existing backoff math unchanged: repeats extend the effective threshold."""
    coordinator = make_diag_coordinator(
        device_type=DEVICE_TYPE_STREAM_MICRO_INVERTER
    )
    coordinator._mqtt_silence_threshold = 90
    clock = {"now": 1_000_000.0}
    monkeypatch.setattr(time, "time", lambda: clock["now"])
    coordinator._last_mqtt_message_time = clock["now"] - 120
    await coordinator._mqtt_watchdog_tick()
    assert coordinator.mqtt_silent_reconnects == 1
    clock["now"] += 120
    before = coordinator._mqtt_client.disconnects
    await coordinator._mqtt_watchdog_tick()
    assert coordinator._mqtt_client.disconnects == before
    assert coordinator.mqtt_silent_reconnects == 1


# --- HA wiring ---------------------------------------------------------------

async def test_diagnostics_available_without_telemetry_or_rest() -> None:
    coordinator = make_diag_coordinator()
    coordinator.data = None
    coordinator.last_update_success = False
    last = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    counter = EcoFlowSilentReconnectsSensor(coordinator, make_entry())
    assert last.available is True
    assert counter.available is True
    assert last.native_value is None  # HA renders unknown
    assert counter.native_value == 0


async def test_diagnostic_entities_write_only_on_change() -> None:
    coordinator = make_diag_coordinator()
    last = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    writes: list = []
    last.async_write_ha_state = lambda *a, **k: writes.append(1)  # type: ignore[method-assign]
    last._handle_coordinator_update()  # unchanged None -> no write
    assert writes == []
    coordinator._handle_mqtt_message({"soc": 1})
    last._handle_coordinator_update()  # timestamp changed -> write
    assert writes == [1]
    last._handle_coordinator_update()  # unchanged -> no write
    assert writes == [1]

    counter = EcoFlowSilentReconnectsSensor(coordinator, make_entry())
    counter_writes: list = []
    counter.async_write_ha_state = lambda *a, **k: counter_writes.append(1)  # type: ignore[method-assign]
    counter._handle_coordinator_update()
    assert counter_writes == []
    coordinator._mqtt_silent_reconnects = 2
    coordinator.async_update_mqtt_diagnostics()  # no listeners yet; direct check:
    counter._handle_coordinator_update()
    assert counter_writes == [1]


async def test_last_receipt_publish_is_throttled() -> None:
    """Receipt state is published at most once per interval, first one at once."""
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    interval = sensor_module.MQTT_RECEIPT_PUBLISH_INTERVAL
    coordinator = make_diag_coordinator()
    last = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    writes: list = []
    last.async_write_ha_state = lambda *a, **k: writes.append(1)  # type: ignore[method-assign]

    # First receipt (None -> value) is published immediately.
    coordinator._last_mqtt_telemetry_time = base
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 1

    # Receipts inside the interval are skipped, whichever path delivers them.
    for seconds in (1, 5, 30):
        coordinator._last_mqtt_telemetry_time = base + timedelta(seconds=seconds)
        last._handle_mqtt_diagnostic_update()
        last._handle_coordinator_update()
    just_inside = base + interval - timedelta(seconds=1)
    coordinator._last_mqtt_telemetry_time = just_inside
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 1

    # Exactly one interval after the published value, it is published.
    coordinator._last_mqtt_telemetry_time = base + interval
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 2

    # The window restarts from the newly published value.
    coordinator._last_mqtt_telemetry_time = base + interval + timedelta(seconds=10)
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 2
    coordinator._last_mqtt_telemetry_time = base + 2 * interval
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 3


async def test_last_receipt_backwards_clock_is_published() -> None:
    """A value earlier than the published one (clock step) is not held back."""
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    coordinator = make_diag_coordinator()
    last = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    writes: list = []
    last.async_write_ha_state = lambda *a, **k: writes.append(1)  # type: ignore[method-assign]

    coordinator._last_mqtt_telemetry_time = base
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 1
    coordinator._last_mqtt_telemetry_time = base - timedelta(seconds=5)
    last._handle_mqtt_diagnostic_update()
    assert len(writes) == 2


async def test_silent_reconnect_counter_is_not_throttled() -> None:
    """Every counter change reaches HA at once; only the timestamp is limited."""
    coordinator = make_diag_coordinator()
    counter = EcoFlowSilentReconnectsSensor(coordinator, make_entry())
    writes: list = []
    counter.async_write_ha_state = lambda *a, **k: writes.append(1)  # type: ignore[method-assign]
    for count in (1, 2, 3, 0):
        coordinator._mqtt_silent_reconnects = count
        counter._handle_mqtt_diagnostic_update()
    assert len(writes) == 4


async def test_diagnostic_listener_notifies_without_fanout() -> None:
    coordinator = make_diag_coordinator()
    last = EcoFlowLastMqttMessageSensor(coordinator, make_entry())
    writes: list = []
    last.async_write_ha_state = lambda *a, **k: writes.append(1)  # type: ignore[method-assign]
    remove = coordinator.async_add_mqtt_diagnostic_listener(
        last._handle_mqtt_diagnostic_update
    )
    coordinator._last_mqtt_telemetry_time = datetime.now(timezone.utc)
    coordinator.async_update_mqtt_diagnostics()
    assert writes == [1]
    remove()
    coordinator._last_mqtt_telemetry_time = datetime.now(timezone.utc)
    coordinator.async_update_mqtt_diagnostics()
    assert writes == [1]


async def test_entities_created_only_on_hybrid_coordinator(monkeypatch) -> None:
    """Both diagnostics are created only for supporting (hybrid) coordinators."""
    monkeypatch.setitem(sensor_module.DEVICE_SENSOR_MAP, "TEST84", {})
    added: list = []

    def collect(entities: list, *args: Any, **kwargs: Any) -> None:
        added.extend(entities)

    hass = SimpleNamespace(data={DOMAIN: {}})

    hybrid = make_diag_coordinator()
    entry = make_entry("hybrid84")
    hass.data[DOMAIN][entry.entry_id] = hybrid
    await sensor_module.async_setup_entry(hass, entry, collect)
    hybrid_ids = {e.unique_id for e in added}
    assert "hybrid84_last_mqtt_message_received" in hybrid_ids
    assert "hybrid84_consecutive_silent_watchdog_reconnects" in hybrid_ids

    added.clear()
    rest = object.__new__(EcoFlowDataCoordinator)
    rest.device_sn = "TESTDEVICE01"
    rest.device_type = DEVICE_TYPE_DELTA_PRO_3
    rest.data = {}
    rest.last_update_success = True
    rest_entry = make_entry("rest84")
    hass.data[DOMAIN][rest_entry.entry_id] = rest
    await sensor_module.async_setup_entry(hass, rest_entry, collect)
    rest_ids = {e.unique_id for e in added}
    assert "rest84_last_mqtt_message_received" not in rest_ids
    assert "rest84_consecutive_silent_watchdog_reconnects" not in rest_ids


# --- malformed payloads ------------------------------------------------------

async def test_malformed_quota_params_never_advance_timestamp() -> None:
    """Null/string/list/numeric quota params must not advance the receipt clock."""
    for bad_params in (None, "oops", [1, 2], 42):
        coordinator = make_diag_coordinator()
        client = EcoFlowMQTTClient(
            username="u",
            password="p",
            device_sn="SN",
            certificate_account="ACC",
            on_message_callback=(
                lambda payload, is_telemetry=True: coordinator._handle_mqtt_message(
                    payload, is_telemetry=is_telemetry
                )
            ),
        )
        client._on_message(
            None, None, _msg("/open/ACC/SN/quota", {"params": bad_params})
        )
        assert coordinator.last_mqtt_message_received is None

    # Non-dict payloads passed directly behave the same way.
    coordinator = make_diag_coordinator()
    for bad_payload in (None, "oops", [1, 2], 42):
        coordinator._handle_mqtt_message(bad_payload)
    assert coordinator.last_mqtt_message_received is None

    # The handler still accepts the next valid message afterwards.
    coordinator._handle_mqtt_message({"soc": 1})
    assert coordinator.last_mqtt_message_received is not None


async def test_malformed_json_never_reaches_telemetry() -> None:
    """Undecodable MQTT payloads never reach the telemetry callback."""
    seen: list = []
    client = EcoFlowMQTTClient(
        username="u",
        password="p",
        device_sn="SN",
        certificate_account="ACC",
        on_message_callback=lambda payload, is_telemetry=True: seen.append(
            (payload, is_telemetry)
        ),
    )
    client._on_message(
        None,
        None,
        SimpleNamespace(topic="/open/ACC/SN/quota", payload=b"\xff\xfe not json"),
    )
    assert seen == []
