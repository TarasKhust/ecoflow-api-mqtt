"""Exercise Stream Microinverter state writes through the MQTT listener path."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame

from custom_components.ecoflow_api.const import DEVICE_TYPE_STREAM_MICRO_INVERTER
from custom_components.ecoflow_api.hybrid_coordinator import EcoFlowHybridCoordinator
from custom_components.ecoflow_api.sensor import (
    STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
    EcoFlowStreamMicroSensor,
)


async def test_mqtt_only_writes_changed_stream_micro_readings(tmp_path, monkeypatch):
    hass = HomeAssistant(str(tmp_path))
    # The coordinator uses HA's implicit config entry in this isolated test.
    monkeypatch.setattr(frame, "report_usage", Mock())
    coordinator = EcoFlowHybridCoordinator(
        hass, Mock(), "test-device", DEVICE_TYPE_STREAM_MICRO_INVERTER
    )
    sensors = []
    remove_listeners = []
    for sensor_id, definition in STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS.items():
        sensor = EcoFlowStreamMicroSensor(
            coordinator, SimpleNamespace(entry_id="test-entry"), sensor_id, definition
        )
        sensor.async_write_ha_state = Mock()
        sensors.append(sensor)
        remove_listeners.append(
            coordinator.async_add_listener(sensor._handle_coordinator_update)
        )

    async def receive(payload):
        coordinator._handle_mqtt_message(payload)
        await asyncio.sleep(0)

    def writes():
        return sum(sensor.async_write_ha_state.call_count for sensor in sensors)

    try:
        await receive({"powGetPv": 100, "powGetPv2": 30})
        assert writes() == len(sensors)
        await receive({"powGetPv": 100, "powGetPv2": 30})
        assert writes() == len(sensors)
        await receive({"powGetPv": 110})
        assert writes() == len(sensors) + 1
        assert sensors[0].native_value == 110

        # A REST publication still reports steady readings. A failure and a
        # subsequent MQTT recovery must notify all the sensors.
        coordinator.async_set_updated_data(coordinator.data)
        assert writes() == 2 * len(sensors) + 1
        coordinator.last_update_success = False
        coordinator.async_update_listeners()
        assert all(not sensor.available for sensor in sensors)
        await receive({"powGetPv": 110})
        assert all(sensor.available for sensor in sensors)
        assert writes() == 4 * len(sensors) + 1
    finally:
        for remove in remove_listeners:
            remove()
        await coordinator.async_shutdown()
