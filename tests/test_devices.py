"""Tests for device registry and profiles."""

from __future__ import annotations

import pytest

from custom_components.ecoflow_api.commands.base import CommandFormat
from custom_components.ecoflow_api.devices import get_all_profiles, get_device_types, get_profile
from custom_components.ecoflow_api.devices.base import (
    DeviceProfile,
    EcoFlowBinarySensorDef,
    EcoFlowButtonDef,
    EcoFlowNumberDef,
    EcoFlowSelectDef,
    EcoFlowSensorDef,
    EcoFlowSwitchDef,
)

# All expected device types
EXPECTED_DEVICES = {
    "delta_pro_3": ("Delta Pro 3", CommandFormat.PRO_V2),
    "delta_pro": ("Delta Pro", CommandFormat.PRO_V1),
    "delta_2": ("Delta 2", CommandFormat.DELTA_V2),
    "stream_ultra_x": ("Stream Ultra X", CommandFormat.PRO_V2),
    "smart_plug": ("Smart Plug S401", CommandFormat.SMART_PLUG),
}


class TestDeviceRegistry:
    """Test device registry functions."""

    def test_get_profile_returns_profile(self):
        for device_type in EXPECTED_DEVICES:
            profile = get_profile(device_type)
            assert profile is not None, f"Profile not found for {device_type}"
            assert isinstance(profile, DeviceProfile)

    def test_get_profile_unknown_returns_none(self):
        assert get_profile("nonexistent_device") is None

    def test_get_device_types_returns_all(self):
        types = get_device_types()
        assert len(types) == len(EXPECTED_DEVICES)
        for device_type, (display_name, _) in EXPECTED_DEVICES.items():
            assert device_type in types
            assert types[device_type] == display_name

    def test_get_all_profiles_returns_dict(self):
        profiles = get_all_profiles()
        assert isinstance(profiles, dict)
        assert len(profiles) == len(EXPECTED_DEVICES)

    def test_get_all_profiles_returns_copy(self):
        """Ensure get_all_profiles returns a copy, not the internal dict."""
        profiles1 = get_all_profiles()
        profiles2 = get_all_profiles()
        assert profiles1 is not profiles2


class TestDeviceProfiles:
    """Test individual device profiles."""

    @pytest.fixture(params=list(EXPECTED_DEVICES.keys()))
    def profile(self, request):
        """Parametrized fixture that yields each device profile."""
        return get_profile(request.param)

    def test_profile_has_required_fields(self, profile):
        assert profile.device_type in EXPECTED_DEVICES
        assert profile.display_name
        assert isinstance(profile.command_format, CommandFormat)

    def test_profile_command_format_matches(self, profile):
        _, expected_format = EXPECTED_DEVICES[profile.device_type]
        assert profile.command_format == expected_format

    def test_profile_has_sensors(self, profile):
        """Every device should have at least some sensors."""
        assert len(profile.sensors) > 0, f"{profile.device_type} has no sensors"

    def test_profile_sensor_types(self, profile):
        for sensor in profile.sensors:
            assert isinstance(sensor, EcoFlowSensorDef)

    def test_profile_switch_types(self, profile):
        for switch in profile.switches:
            assert isinstance(switch, EcoFlowSwitchDef)

    def test_profile_number_types(self, profile):
        for number in profile.numbers:
            assert isinstance(number, EcoFlowNumberDef)

    def test_profile_select_types(self, profile):
        for select in profile.selects:
            assert isinstance(select, EcoFlowSelectDef)

    def test_profile_binary_sensor_types(self, profile):
        for bs in profile.binary_sensors:
            assert isinstance(bs, EcoFlowBinarySensorDef)

    def test_profile_button_types(self, profile):
        for button in profile.buttons:
            assert isinstance(button, EcoFlowButtonDef)


class TestEntityKeyUniqueness:
    """Test that entity keys are unique within each platform per device."""

    @pytest.fixture(params=list(EXPECTED_DEVICES.keys()))
    def profile(self, request):
        return get_profile(request.param)

    def _assert_unique_keys(self, items, platform_name, device_type):
        keys = [item.key for item in items]
        duplicates = [k for k in keys if keys.count(k) > 1]
        assert not duplicates, f"Duplicate {platform_name} keys in {device_type}: {set(duplicates)}"

    def test_sensor_keys_unique(self, profile):
        self._assert_unique_keys(profile.sensors, "sensor", profile.device_type)

    def test_switch_keys_unique(self, profile):
        self._assert_unique_keys(profile.switches, "switch", profile.device_type)

    def test_number_keys_unique(self, profile):
        self._assert_unique_keys(profile.numbers, "number", profile.device_type)

    def test_select_keys_unique(self, profile):
        self._assert_unique_keys(profile.selects, "select", profile.device_type)

    def test_binary_sensor_keys_unique(self, profile):
        self._assert_unique_keys(profile.binary_sensors, "binary_sensor", profile.device_type)

    def test_button_keys_unique(self, profile):
        self._assert_unique_keys(profile.buttons, "button", profile.device_type)


class TestEntityDefinitionConstraints:
    """Test that entity definitions follow project conventions."""

    @pytest.fixture(params=list(EXPECTED_DEVICES.keys()))
    def profile(self, request):
        return get_profile(request.param)

    def test_sensor_keys_are_snake_case(self, profile):
        for sensor in profile.sensors:
            assert sensor.key == sensor.key.lower(), (
                f"Sensor key '{sensor.key}' in {profile.device_type} is not lowercase"
            )
            assert " " not in sensor.key, f"Sensor key '{sensor.key}' in {profile.device_type} contains spaces"

    def test_switch_keys_are_snake_case(self, profile):
        for switch in profile.switches:
            assert switch.key == switch.key.lower(), (
                f"Switch key '{switch.key}' in {profile.device_type} is not lowercase"
            )
            assert " " not in switch.key

    def test_number_keys_are_snake_case(self, profile):
        for number in profile.numbers:
            assert number.key == number.key.lower(), (
                f"Number key '{number.key}' in {profile.device_type} is not lowercase"
            )

    def test_sensors_have_state_key(self, profile):
        for sensor in profile.sensors:
            assert sensor.state_key, f"Sensor '{sensor.key}' in {profile.device_type} has empty state_key"

    def test_switches_have_param_key(self, profile):
        for switch in profile.switches:
            assert switch.param_key, f"Switch '{switch.key}' in {profile.device_type} has empty param_key"

    def test_numbers_have_valid_range(self, profile):
        for number in profile.numbers:
            assert number.min_value <= number.max_value, (
                f"Number '{number.key}' in {profile.device_type}: "
                f"min_value ({number.min_value}) > max_value ({number.max_value})"
            )
            assert number.step > 0, f"Number '{number.key}' in {profile.device_type}: step must be positive"

    def test_selects_have_options(self, profile):
        for select in profile.selects:
            assert select.options, f"Select '{select.key}' in {profile.device_type} has no options"
            assert len(select.options) >= 2, f"Select '{select.key}' in {profile.device_type} needs at least 2 options"

    def test_switch_state_interpreter_valid(self, profile):
        valid_interpreters = {"bool", "int01", "flow_info"}
        for switch in profile.switches:
            assert switch.state_interpreter in valid_interpreters, (
                f"Switch '{switch.key}' in {profile.device_type} has invalid "
                f"state_interpreter '{switch.state_interpreter}'"
            )


class TestFrozenDataclasses:
    """Test that entity definitions are immutable."""

    def test_sensor_def_is_frozen(self):
        sensor = EcoFlowSensorDef(key="test", name="Test", state_key="testKey")
        with pytest.raises(AttributeError):
            sensor.key = "modified"

    def test_switch_def_is_frozen(self):
        switch = EcoFlowSwitchDef(key="test", name="Test", state_key="testKey", param_key="testParam")
        with pytest.raises(AttributeError):
            switch.key = "modified"

    def test_number_def_is_frozen(self):
        number = EcoFlowNumberDef(key="test", name="Test", state_key="testKey", param_key="testParam")
        with pytest.raises(AttributeError):
            number.key = "modified"

    def test_select_def_is_frozen(self):
        select = EcoFlowSelectDef(key="test", name="Test", param_key="testParam", options={"A": 1, "B": 2})
        with pytest.raises(AttributeError):
            select.key = "modified"

    def test_binary_sensor_def_is_frozen(self):
        bs = EcoFlowBinarySensorDef(key="test", name="Test", state_key="testKey")
        with pytest.raises(AttributeError):
            bs.key = "modified"

    def test_button_def_is_frozen(self):
        button = EcoFlowButtonDef(key="test", name="Test", param_key="testParam")
        with pytest.raises(AttributeError):
            button.key = "modified"
