"""Coverage for per-unit Stream sensors (bmsBattSoc/outputWatts/role)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower

from custom_components.ecoflow_api.sensor import (
    DEVICE_SENSOR_MAP,
    POWERSTREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
    STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
    EcoFlowSensor,
)

STREAM_ALIASES = (
    "stream_ultra_x",
    "stream_ultra",
    "Stream Ultra",
    "Stream Ultra X",
    "stream_ac_pro",
    "Stream AC Pro",
)

UNIT_IDS = ("unit_battery_level", "unit_output_power", "unit_role")

EXPECTED = {
    "unit_battery_level": {
        "name": "Unit Battery Level",
        "key": "bmsBattSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart-variant",
    },
    "unit_output_power": {
        "name": "Unit Output Power",
        "key": "outputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash-outline",
    },
    "unit_role": {
        "name": "Unit Role",
        "key": "distributedDeviceStatus",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:crown-outline",
    },
}


def _sensor(
    sensor_id: str, data: dict | None, alias: str = "Stream Ultra X"
) -> EcoFlowSensor:
    definition = DEVICE_SENSOR_MAP[alias][sensor_id]
    coordinator = SimpleNamespace(
        device_sn="SN1",
        device_type=alias,
        last_update_success=True,
        data=data,
    )
    entry = SimpleNamespace(entry_id="entry1")
    return EcoFlowSensor(
        coordinator=coordinator,
        entry=entry,
        sensor_id=sensor_id,
        sensor_config=definition,
    )


def _assert_definition(definition: dict, sensor_id: str) -> None:
    expected = EXPECTED[sensor_id]
    assert definition["name"] == expected["name"]
    assert definition["key"] == expected["key"]
    assert definition.get("unit") == expected["unit"]
    assert definition.get("device_class") == expected["device_class"]
    assert definition.get("state_class") == expected["state_class"]
    assert definition["icon"] == expected["icon"]


@pytest.mark.parametrize("alias", STREAM_ALIASES)
def test_all_stream_aliases_expose_unit_sensors(alias: str) -> None:
    for sensor_id in UNIT_IDS:
        assert sensor_id in DEVICE_SENSOR_MAP[alias]
        _assert_definition(DEVICE_SENSOR_MAP[alias][sensor_id], sensor_id)


def test_profiles_without_unit_sensors_unaffected() -> None:
    for profile in (
        POWERSTREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
        STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
    ):
        for sensor_id in UNIT_IDS:
            assert sensor_id not in profile


@pytest.mark.parametrize("alias", ["stream_ultra_x", "stream_ac_pro"])
@pytest.mark.parametrize("sensor_id", UNIT_IDS)
def test_entity_metadata_uses_actual_sensor_id(sensor_id: str, alias: str) -> None:
    expected = EXPECTED[sensor_id]
    _assert_definition(DEVICE_SENSOR_MAP[alias][sensor_id], sensor_id)
    sensor = _sensor(sensor_id, {}, alias)
    assert sensor._sensor_id == sensor_id
    assert sensor._attr_name == expected["name"]
    assert sensor.translation_key == sensor_id
    assert sensor.unique_id == f"entry1_{sensor_id}"
    assert sensor.native_unit_of_measurement == expected["unit"]
    assert sensor.device_class == expected["device_class"]
    assert sensor.state_class == expected["state_class"]
    assert sensor.icon == expected["icon"]


def test_unit_values_ignore_contradictory_system_fields() -> None:
    data = {
        "bmsBattSoc": 83,
        "cmsBattSoc": 99,
        "actSoc": 55,
        "outputWatts": 42.5,
        "powGetSysLoad": 600,
    }
    assert _sensor("unit_battery_level", data).native_value == 83
    assert _sensor("unit_output_power", data).native_value == 42.5


@pytest.mark.parametrize("value", [0, 0.0, 0.5, 6.25, 1500])
def test_unit_output_power_preserves_zero_and_fractions(value: float) -> None:
    data = {"outputWatts": value, "powGetSysLoad": 999}
    assert _sensor("unit_output_power", data).native_value == value


@pytest.mark.parametrize("value", [0, 0.0])
def test_unit_battery_zero_not_replaced_by_system_fields(value: float) -> None:
    data = {"bmsBattSoc": value, "cmsBattSoc": 77, "actSoc": 66}
    assert _sensor("unit_battery_level", data).native_value == value


def test_missing_or_none_unit_fields_stay_unknown() -> None:
    sensor_map = {
        "bmsBattSoc": "unit_battery_level",
        "outputWatts": "unit_output_power",
        "distributedDeviceStatus": "unit_role",
    }
    for key, sensor_id in sensor_map.items():
        for data in (None, {}, {"cmsBattSoc": 88, "powGetSysLoad": 500}):
            assert _sensor(sensor_id, data).native_value is None
            assert _sensor(sensor_id, (data or {}) | {key: None}).native_value is None


@pytest.mark.parametrize("role", ["MASTER", "SLAVE", "ELECTION", " NEW-STATE "])
def test_unit_role_preserves_raw_strings(role: str) -> None:
    data = {"distributedDeviceStatus": role, "bmsBattSoc": 10}
    assert _sensor("unit_role", data).native_value == role


def test_same_instance_reflects_role_and_reading_changes() -> None:
    sensor = _sensor("unit_role", {"distributedDeviceStatus": "MASTER"})
    assert sensor.native_value == "MASTER"
    sensor.coordinator.data = {"distributedDeviceStatus": "SLAVE", "outputWatts": 12}
    assert sensor.native_value == "SLAVE"
    power = _sensor("unit_output_power", {"outputWatts": 1.5})
    assert power.native_value == 1.5
    power.coordinator.data = {"outputWatts": 0}
    assert power.native_value == 0
    power.coordinator.data = {}
    assert power.native_value is None


@pytest.mark.parametrize(
    ("sensor_id", "data", "expected"),
    [
        ("battery_level", {"cmsBattSoc": 64, "actSoc": 40}, 64),
        ("battery_level", {"cmsBattSoc": 0, "actSoc": 40}, 40),
        ("battery_level", {"actSoc": 0}, 0),
        ("system_load_power", {"powGetSysLoad": 300, "outputWatts": 10}, 300),
        ("system_load_power", {"powGetSysLoad": 0, "outputWatts": 10}, 10),
        ("system_load_power", {"outputWatts": 0}, 0),
    ],
)
def test_existing_aggregate_fallback_semantics_preserved(
    sensor_id: str, data: dict, expected: float
) -> None:
    assert _sensor(sensor_id, data).native_value == expected
