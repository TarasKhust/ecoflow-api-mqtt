"""Live state-machine coverage for the MQTT diagnostic entities."""

from __future__ import annotations

import logging
import time
from datetime import timedelta, timezone
from types import SimpleNamespace
from typing import Any

from custom_components.ecoflow_api.const import DEVICE_TYPE_DELTA_PRO_3
from custom_components.ecoflow_api.hybrid_coordinator import EcoFlowHybridCoordinator
from custom_components.ecoflow_api.sensor import (
    EcoFlowLastMqttMessageSensor,
    EcoFlowSilentReconnectsSensor,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.util import dt as dt_util


class FakeMqttTransportClient:
    """Record watchdog disconnects without touching the network."""

    def __init__(self) -> None:
        self.disconnects = 0

    async def async_disconnect(self) -> None:
        self.disconnects += 1


async def _add_live_entities(hass: HomeAssistant, entities: list) -> None:
    """Add entities through a real entity platform (no integration setup)."""
    platform = EntityPlatform(
        hass=hass,
        logger=logging.getLogger(__name__),
        domain="sensor",
        platform_name="ecoflow_api",
        platform=None,
        scan_interval=timedelta(seconds=30),
        entity_namespace=None,
    )
    await platform.async_add_entities(entities)


async def test_real_coordinator_initial_diagnostics(hass: HomeAssistant) -> None:
    """A real hybrid coordinator starts with unknown receipt and zero count."""
    coordinator = EcoFlowHybridCoordinator(
        hass=hass,
        client=SimpleNamespace(),
        device_sn="TESTDEVICE01",
        device_type=DEVICE_TYPE_DELTA_PRO_3,
        update_interval=15,
    )
    assert coordinator.last_mqtt_message_received is None
    assert coordinator.mqtt_silent_reconnects == 0


async def test_async_setup_mqtt_baseline_without_receipt(
    hass: HomeAssistant, monkeypatch: Any
) -> None:
    """Real _async_setup_mqtt: connect/reconnect resets baseline, never receipt."""

    class FakeSuccessMqtt:
        """Accept the coordinator's wiring without touching the network."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.init_kwargs = kwargs

        async def async_connect(self) -> bool:
            return True

        async def async_disconnect(self) -> None:
            return None

    import custom_components.ecoflow_api.hybrid_coordinator as hybrid_module

    monkeypatch.setattr(hybrid_module, "EcoFlowMQTTClient", FakeSuccessMqtt)
    coordinator = EcoFlowHybridCoordinator(
        hass=hass,
        client=SimpleNamespace(),
        device_sn="TESTDEVICE02",
        device_type=DEVICE_TYPE_DELTA_PRO_3,
        update_interval=15,
        mqtt_username="user",
        mqtt_password="password",
    )
    assert coordinator._last_mqtt_message_time is None

    # Initial broker connect: baseline starts, receipt stays None.
    await coordinator._async_setup_mqtt()
    assert coordinator.mqtt_connected is True
    assert coordinator.last_mqtt_message_received is None
    first_baseline = coordinator._last_mqtt_message_time
    assert first_baseline is not None

    # Reconnect after telemetry: baseline resets, receipt object unchanged.
    coordinator._handle_mqtt_message({"soc": 5})
    await hass.async_block_till_done()
    receipt = coordinator.last_mqtt_message_received
    assert receipt is not None
    coordinator._last_mqtt_message_time = first_baseline - 5000
    coordinator._mqtt_connected = False
    await coordinator._async_setup_mqtt()
    assert coordinator.last_mqtt_message_received is receipt
    assert coordinator._last_mqtt_message_time is not None
    assert coordinator._last_mqtt_message_time > first_baseline - 5000

    await coordinator.async_shutdown()


async def test_diagnostics_live_state_machine(hass: HomeAssistant) -> None:
    """End-to-end through hass.states: setup, telemetry, failed watchdog tick."""
    coordinator = EcoFlowHybridCoordinator(
        hass=hass,
        client=SimpleNamespace(),
        device_sn="TESTDEVICE03",
        device_type=DEVICE_TYPE_DELTA_PRO_3,
        update_interval=15,
    )
    entry = SimpleNamespace(entry_id="testha84")
    last = EcoFlowLastMqttMessageSensor(coordinator, entry)
    counter = EcoFlowSilentReconnectsSensor(coordinator, entry)
    await _add_live_entities(hass, [last, counter])
    await hass.async_block_till_done()
    last_id = last.entity_id
    counter_id = counter.entity_id

    assert hass.states.get(last_id).state == "unknown"
    assert hass.states.get(counter_id).state == "0"

    # Live quota telemetry flows through coordinator subscriptions to states.
    coordinator._handle_mqtt_message({"soc": 10})
    await hass.async_block_till_done()
    timestamp_state = hass.states.get(last_id).state
    received = dt_util.parse_datetime(timestamp_state)
    assert received is not None and received.tzinfo is not None
    assert received.utcoffset() == timezone.utc.utcoffset(None)

    # Watchdog increment with a failed reconnect while REST is down: the
    # counter still reaches HA, the timestamp is untouched, and both stay
    # available.
    coordinator.last_update_success = False
    coordinator.data = None
    coordinator._mqtt_client = FakeMqttTransportClient()
    coordinator._mqtt_connected = True
    coordinator._last_mqtt_message_time = time.time() - 10000

    async def failing_setup() -> None:
        coordinator._mqtt_connected = False

    coordinator._async_setup_mqtt = failing_setup  # type: ignore[method-assign]
    await coordinator._mqtt_watchdog_tick()
    await hass.async_block_till_done()
    assert hass.states.get(counter_id).state == "1"
    assert hass.states.get(last_id).state == timestamp_state
    assert last.available is True
    assert counter.available is True

    # Unchanged coordinator and diagnostic notifications cause no extra writes.
    writes = {"count": 0}
    for entity in (last, counter):
        original = entity.async_write_ha_state

        def counting(*args: Any, _original: Any = original, **kwargs: Any) -> Any:
            writes["count"] += 1
            return _original(*args, **kwargs)

        entity.async_write_ha_state = counting  # type: ignore[method-assign]
    coordinator.async_update_mqtt_diagnostics()
    coordinator.async_update_listeners()
    await hass.async_block_till_done()
    assert writes["count"] == 0

    # Removing an entity cleans up its diagnostic listener.
    assert len(coordinator._mqtt_diagnostic_listeners) == 2
    await last.async_remove()
    assert len(coordinator._mqtt_diagnostic_listeners) == 1
    coordinator.async_update_mqtt_diagnostics()
    await hass.async_block_till_done()
    assert writes["count"] == 0

    coordinator._shutting_down = True
    if coordinator._mqtt_watchdog_timer is not None:
        coordinator._mqtt_watchdog_timer.cancel()
