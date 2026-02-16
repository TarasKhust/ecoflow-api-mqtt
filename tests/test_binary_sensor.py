"""Tests for binary sensor platform entity logic."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.ecoflow_api.binary_sensor import (
    EcoFlowBinarySensor,
    EcoFlowExtraBatteryBinarySensor,
    _detect_extra_batteries,
    _get_battery_number,
)
from custom_components.ecoflow_api.devices.base import EcoFlowBinarySensorDef


def _make_binary_sensor(coordinator, **kwargs):
    """Helper to create an EcoFlowBinarySensor with a definition."""
    defaults = {
        "key": "test_binary",
        "name": "Test Binary",
        "state_key": "testState",
    }
    defaults.update(kwargs)
    defn = EcoFlowBinarySensorDef(**defaults)
    return EcoFlowBinarySensor(coordinator, defn)


class TestDetectExtraBatteries:
    """Test _detect_extra_batteries helper."""

    def test_no_data(self):
        assert _detect_extra_batteries({}) == []
        assert _detect_extra_batteries(None) == []

    def test_no_extra_batteries(self):
        data = {"bmsBattSoc": 50, "powInSumW": 100}
        assert _detect_extra_batteries(data) == []

    def test_detect_slave1(self):
        data = {"slave1BattSoc": 80, "slave1Temp": 25}
        assert _detect_extra_batteries(data) == ["slave1"]

    def test_detect_multiple(self):
        data = {
            "slave1BattSoc": 80,
            "slave2BattSoc": 70,
            "bms2Temp": 30,
        }
        result = _detect_extra_batteries(data)
        assert "slave1" in result
        assert "slave2" in result
        assert "bms2" in result

    def test_results_sorted(self):
        data = {
            "slave2BattSoc": 70,
            "bms2Temp": 30,
            "slave1BattSoc": 80,
        }
        result = _detect_extra_batteries(data)
        assert result == sorted(result)

    def test_no_duplicates(self):
        data = {"slave1BattSoc": 80, "slave1Temp": 25, "slave1Watts": 100}
        result = _detect_extra_batteries(data)
        assert result == ["slave1"]


class TestGetBatteryNumber:
    """Test _get_battery_number helper."""

    def test_slave1(self):
        assert _get_battery_number("slave1") == 1

    def test_slave2(self):
        assert _get_battery_number("slave2") == 2

    def test_bms3(self):
        assert _get_battery_number("bms3") == 3

    def test_eb1(self):
        assert _get_battery_number("eb1") == 1

    def test_no_number(self):
        assert _get_battery_number("extraBms") == 1

    def test_slave_battery(self):
        assert _get_battery_number("slaveBattery") == 1


class TestBinarySensorDirectState:
    """Test EcoFlowBinarySensor with direct state reading."""

    def test_bool_true(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is True

    def test_bool_false(self, mock_coordinator):
        mock_coordinator.data = {"testState": False}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is False

    def test_int_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is True

    def test_int_0(self, mock_coordinator):
        mock_coordinator.data = {"testState": 0}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is False

    def test_string_true(self, mock_coordinator):
        mock_coordinator.data = {"testState": "1"}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is True

    def test_string_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": "on"}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is True

    def test_none_data(self, mock_coordinator):
        mock_coordinator.data = None
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is None

    def test_missing_key(self, mock_coordinator):
        mock_coordinator.data = {"other": True}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is None

    def test_none_value(self, mock_coordinator):
        mock_coordinator.data = {"testState": None}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is None

    def test_unsupported_type(self, mock_coordinator):
        mock_coordinator.data = {"testState": [1, 2, 3]}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.is_on is None


class TestBinarySensorDerived:
    """Test derived binary sensors."""

    def test_derived_with_condition(self, mock_coordinator):
        mock_coordinator.data = {"battSoc": 15}
        sensor = _make_binary_sensor(
            mock_coordinator,
            state_key="battSoc",
            derived=True,
            derive_from="battSoc",
            derive_condition=lambda v: v is not None and v < 20,
        )
        assert sensor.is_on is True

    def test_derived_condition_false(self, mock_coordinator):
        mock_coordinator.data = {"battSoc": 50}
        sensor = _make_binary_sensor(
            mock_coordinator,
            state_key="battSoc",
            derived=True,
            derive_from="battSoc",
            derive_condition=lambda v: v is not None and v < 20,
        )
        assert sensor.is_on is False

    def test_derived_no_condition(self, mock_coordinator):
        mock_coordinator.data = {"battSoc": 50}
        sensor = _make_binary_sensor(
            mock_coordinator,
            state_key="battSoc",
            derived=True,
            derive_from="battSoc",
        )
        assert sensor.is_on is None


class TestBinarySensorIcon:
    """Test icon property."""

    def test_icon_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        sensor = _make_binary_sensor(
            mock_coordinator,
            icon_on="mdi:check",
            icon_off="mdi:close",
        )
        assert sensor.icon == "mdi:check"

    def test_icon_off(self, mock_coordinator):
        mock_coordinator.data = {"testState": False}
        sensor = _make_binary_sensor(
            mock_coordinator,
            icon_on="mdi:check",
            icon_off="mdi:close",
        )
        assert sensor.icon == "mdi:close"

    def test_default_icons(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        sensor = _make_binary_sensor(mock_coordinator)
        assert sensor.icon == "mdi:check-circle"


class TestExtraBatteryBinarySensor:
    """Test EcoFlowExtraBatteryBinarySensor."""

    def _make_extra_battery_sensor(self, coordinator, sensor_key="connected"):
        sensor_defs = {
            "connected": {
                "name": "Connected",
                "device_class": BinarySensorDeviceClass.CONNECTIVITY,
                "icon_on": "mdi:battery-plus",
                "icon_off": "mdi:battery-off",
                "check_key": "Soc",
            },
            "battery_low": {
                "name": "Battery Low",
                "device_class": BinarySensorDeviceClass.BATTERY,
                "icon_on": "mdi:battery-alert",
                "icon_off": "mdi:battery",
                "check_key": "Soc",
                "condition": lambda v: v is not None and v < 20,
            },
        }
        return EcoFlowExtraBatteryBinarySensor(
            coordinator,
            battery_prefix="slave1",
            battery_number=1,
            sensor_key=sensor_key,
            sensor_def=sensor_defs[sensor_key],
        )

    def test_connected_when_data_present(self, mock_coordinator):
        mock_coordinator.data = {"slave1Soc": 80}
        sensor = self._make_extra_battery_sensor(mock_coordinator, "connected")
        assert sensor.is_on is True

    def test_disconnected_when_data_missing(self, mock_coordinator):
        mock_coordinator.data = {"bmsBattSoc": 80}
        sensor = self._make_extra_battery_sensor(mock_coordinator, "connected")
        assert sensor.is_on is False

    def test_battery_low_true(self, mock_coordinator):
        mock_coordinator.data = {"slave1Soc": 10}
        sensor = self._make_extra_battery_sensor(mock_coordinator, "battery_low")
        assert sensor.is_on is True

    def test_battery_low_false(self, mock_coordinator):
        mock_coordinator.data = {"slave1Soc": 50}
        sensor = self._make_extra_battery_sensor(mock_coordinator, "battery_low")
        assert sensor.is_on is False

    def test_extra_state_attributes(self, mock_coordinator):
        mock_coordinator.data = {"slave1Soc": 80}
        sensor = self._make_extra_battery_sensor(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["battery_number"] == 1
        assert attrs["battery_prefix"] == "slave1"

    def test_unique_id(self, mock_coordinator):
        mock_coordinator.data = {}
        sensor = self._make_extra_battery_sensor(mock_coordinator)
        assert sensor.unique_id == "test_entry_id_123_extra_battery_1_connected"

    def test_name(self, mock_coordinator):
        mock_coordinator.data = {}
        sensor = self._make_extra_battery_sensor(mock_coordinator)
        assert sensor.name == "Extra Battery 1 Connected"
