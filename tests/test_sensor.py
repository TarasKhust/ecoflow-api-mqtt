"""Tests for sensor platform entity logic."""

from __future__ import annotations

import struct
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

from custom_components.ecoflow_api.devices.base import EcoFlowSensorDef
from custom_components.ecoflow_api.sensor import EcoFlowSensor


def _make_sensor(coordinator, **kwargs):
    """Helper to create an EcoFlowSensor with a definition."""
    defaults = {
        "key": "test_sensor",
        "name": "Test Sensor",
        "state_key": "testValue",
    }
    defaults.update(kwargs)
    defn = EcoFlowSensorDef(**defaults)
    return EcoFlowSensor(coordinator, defn)


class TestSensorBasicState:
    """Test native_value with basic data types."""

    def test_numeric_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 42}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value == 42

    def test_float_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 3.14}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value == 3.14

    def test_string_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": "hello"}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value == "hello"

    def test_bool_true_returns_on(self, mock_coordinator):
        mock_coordinator.data = {"testValue": True}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value == "on"

    def test_bool_false_returns_off(self, mock_coordinator):
        mock_coordinator.data = {"testValue": False}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value == "off"

    def test_none_data(self, mock_coordinator):
        mock_coordinator.data = None
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value is None

    def test_missing_key(self, mock_coordinator):
        mock_coordinator.data = {"otherKey": 42}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value is None

    def test_none_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": None}
        sensor = _make_sensor(mock_coordinator)
        assert sensor.native_value is None


class TestSensorDottedKeys:
    """Test nested object access via dotted state_key."""

    def test_dotted_key_direct_match(self, mock_coordinator):
        mock_coordinator.data = {"2_1.watts": 150}
        sensor = _make_sensor(mock_coordinator, state_key="2_1.watts")
        assert sensor.native_value == 150

    def test_dotted_key_nested_fallback(self, mock_coordinator):
        mock_coordinator.data = {"parent": {"child": 99}}
        sensor = _make_sensor(mock_coordinator, state_key="parent.child")
        assert sensor.native_value == 99

    def test_dotted_key_missing_parent(self, mock_coordinator):
        mock_coordinator.data = {"other": 1}
        sensor = _make_sensor(mock_coordinator, state_key="parent.child")
        assert sensor.native_value is None


class TestSensorEnumMapping:
    """Test ENUM sensor value mapping."""

    def test_enum_zero_based_index(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 0}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.ENUM,
            options=["Off", "Standby", "Charging"],
        )
        assert sensor.native_value == "Off"

    def test_enum_index_1(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 1}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.ENUM,
            options=["Off", "Standby", "Charging"],
        )
        assert sensor.native_value == "Standby"

    def test_enum_one_based_fallback(self, mock_coordinator):
        """When index >= len(options) but within 1-based range, use idx-1."""
        mock_coordinator.data = {"testValue": 3}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.ENUM,
            options=["Off", "Standby", "Charging"],
        )
        assert sensor.native_value == "Charging"

    def test_enum_out_of_range(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 99}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.ENUM,
            options=["Off", "On"],
        )
        assert sensor.native_value == "99"


class TestSensorResvInfo:
    """Test resvInfo array decoding."""

    def test_resv_float_decode(self, mock_coordinator):
        """Test IEEE 754 float decoding from integer."""
        # Encode 25.5 as IEEE 754 float integer representation
        float_as_int = struct.unpack("I", struct.pack("f", 25.5))[0]
        mock_coordinator.data = {"resvInfo": [0, float_as_int, 0]}
        sensor = _make_sensor(
            mock_coordinator,
            state_key="resvInfo",
            resv_index=1,
            resv_type="float",
        )
        assert sensor.native_value == 25.5

    def test_resv_mah_to_ah(self, mock_coordinator):
        mock_coordinator.data = {"resvInfo": [0, 5000, 0]}
        sensor = _make_sensor(
            mock_coordinator,
            state_key="resvInfo",
            resv_index=1,
            resv_type="mah_to_ah",
        )
        assert sensor.native_value == 5.0

    def test_resv_zero_returns_none(self, mock_coordinator):
        mock_coordinator.data = {"resvInfo": [0, 0, 0]}
        sensor = _make_sensor(
            mock_coordinator,
            state_key="resvInfo",
            resv_index=0,
            resv_type="float",
        )
        assert sensor.native_value is None

    def test_resv_index_out_of_range(self, mock_coordinator):
        mock_coordinator.data = {"resvInfo": [1, 2]}
        sensor = _make_sensor(
            mock_coordinator,
            state_key="resvInfo",
            resv_index=5,
            resv_type="float",
        )
        assert sensor.native_value is None

    def test_resv_not_list(self, mock_coordinator):
        mock_coordinator.data = {"resvInfo": "not_a_list"}
        sensor = _make_sensor(
            mock_coordinator,
            state_key="resvInfo",
            resv_index=0,
            resv_type="float",
        )
        assert sensor.native_value is None


class TestSensorTimestamp:
    """Test timestamp parsing."""

    def test_timestamp_from_epoch_seconds(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 1700000000}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_timestamp_from_epoch_ms(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 1700000000000}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        result = sensor.native_value
        assert isinstance(result, datetime)

    def test_timestamp_zero_returns_none(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 0}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        assert sensor.native_value is None

    def test_timestamp_from_iso_string(self, mock_coordinator):
        mock_coordinator.data = {"testValue": "2024-01-01 12:00:00"}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        result = sensor.native_value
        assert isinstance(result, datetime)

    def test_timestamp_invalid_returns_none(self, mock_coordinator):
        mock_coordinator.data = {"testValue": "not_a_date"}
        sensor = _make_sensor(
            mock_coordinator,
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        assert sensor.native_value is None


class TestSensorAttributes:
    """Test sensor attribute initialization."""

    def test_name(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, name="Battery Level")
        assert sensor.name == "Battery Level"

    def test_unit(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, unit="%")
        assert sensor.native_unit_of_measurement == "%"

    def test_device_class(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, device_class=SensorDeviceClass.POWER)
        assert sensor.device_class == SensorDeviceClass.POWER

    def test_state_class(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, state_class=SensorStateClass.MEASUREMENT)
        assert sensor.state_class == SensorStateClass.MEASUREMENT

    def test_icon(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, icon="mdi:battery")
        assert sensor.icon == "mdi:battery"

    def test_entity_category(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, entity_category=EntityCategory.DIAGNOSTIC)
        assert sensor.entity_category == EntityCategory.DIAGNOSTIC

    def test_unique_id(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator, key="bms_batt_soc")
        assert sensor.unique_id == "test_entry_id_123_bms_batt_soc"

    def test_unique_id_uses_entry_id_not_device_sn(self, mock_coordinator):
        """Verify unique_id uses config entry ID (not device_sn) for backward compatibility.

        Changing the unique_id prefix breaks existing HA installations by creating
        duplicate entities. The old code used entry.entry_id, so we must keep it.
        """
        sensor = _make_sensor(mock_coordinator, key="test_key")
        entry_id = mock_coordinator.config_entry.entry_id
        device_sn = mock_coordinator.device_sn
        # Must use entry_id prefix
        assert sensor.unique_id == f"{entry_id}_test_key"
        # Must NOT use device_sn prefix
        assert sensor.unique_id != f"{device_sn}_test_key"

    def test_definition_property(self, mock_coordinator):
        sensor = _make_sensor(mock_coordinator)
        assert sensor.definition.key == "test_sensor"
