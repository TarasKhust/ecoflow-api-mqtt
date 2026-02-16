"""Tests for number platform entity logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.ecoflow_api.commands.base import CommandFormat
from custom_components.ecoflow_api.devices.base import EcoFlowNumberDef
from custom_components.ecoflow_api.number import EcoFlowNumber


def _make_number(
    coordinator,
    entry=None,
    *,
    key="test_number",
    state_key="testValue",
    param_key="cfgTest",
    min_value=0,
    max_value=100,
    step=1,
    unit=None,
    icon=None,
    command_params=None,
    nested_params=None,
    value_to_ui=None,
    value_from_ui=None,
):
    """Helper to create an EcoFlowNumber with a definition."""
    if entry is None:
        entry = MagicMock()
        entry.options = {}

    defn = EcoFlowNumberDef(
        key=key,
        name="Test Number",
        state_key=state_key,
        param_key=param_key,
        min_value=min_value,
        max_value=max_value,
        step=step,
        unit=unit,
        icon=icon,
        command_params=command_params or {},
        nested_params=nested_params,
        value_to_ui=value_to_ui,
        value_from_ui=value_from_ui,
    )
    return EcoFlowNumber(coordinator, entry, defn, CommandFormat.PRO_V2)


class TestNumberNativeValue:
    """Test native_value property."""

    def test_integer_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 50}
        number = _make_number(mock_coordinator)
        assert number.native_value == 50.0

    def test_float_value(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 3.14}
        number = _make_number(mock_coordinator)
        assert number.native_value == 3.14

    def test_string_numeric(self, mock_coordinator):
        mock_coordinator.data = {"testValue": "42"}
        number = _make_number(mock_coordinator)
        assert number.native_value == 42.0

    def test_none_data(self, mock_coordinator):
        mock_coordinator.data = None
        number = _make_number(mock_coordinator)
        assert number.native_value is None

    def test_missing_key(self, mock_coordinator):
        mock_coordinator.data = {"otherKey": 50}
        number = _make_number(mock_coordinator)
        assert number.native_value is None

    def test_invalid_string(self, mock_coordinator):
        mock_coordinator.data = {"testValue": "not_a_number"}
        number = _make_number(mock_coordinator)
        assert number.native_value is None


class TestNumberValueMapping:
    """Test value_to_ui and value_from_ui mapping functions."""

    def test_value_to_ui(self, mock_coordinator):
        """Test brightness mapping: 0-1023 -> 0-100%."""
        mock_coordinator.data = {"testValue": 512}
        number = _make_number(
            mock_coordinator,
            value_to_ui=lambda v: round(v / 1023 * 100),
        )
        assert number.native_value == 50.0

    def test_value_to_ui_zero(self, mock_coordinator):
        mock_coordinator.data = {"testValue": 0}
        number = _make_number(
            mock_coordinator,
            value_to_ui=lambda v: round(v / 1023 * 100),
        )
        assert number.native_value == 0.0

    async def test_value_from_ui(self, mock_coordinator):
        """Test brightness mapping: 0-100% -> 0-1023."""
        number = _make_number(
            mock_coordinator,
            min_value=0,
            max_value=100,
            value_from_ui=lambda v: round(v / 100 * 1023),
        )
        await number.async_set_native_value(50)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        # 50% -> round(50/100*1023) = 512, then int() = 512
        assert payload["params"]["cfgTest"] == 512


class TestNumberSetValue:
    """Test async_set_native_value."""

    async def test_set_basic_value(self, mock_coordinator):
        number = _make_number(mock_coordinator)
        await number.async_set_native_value(75)
        mock_coordinator.async_send_command.assert_called_once()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] == 75

    async def test_value_clamped_to_min(self, mock_coordinator):
        number = _make_number(mock_coordinator, min_value=10, max_value=90)
        await number.async_set_native_value(5)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] == 10

    async def test_value_clamped_to_max(self, mock_coordinator):
        number = _make_number(mock_coordinator, min_value=10, max_value=90)
        await number.async_set_native_value(100)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] == 90

    async def test_value_converted_to_int(self, mock_coordinator):
        number = _make_number(mock_coordinator)
        await number.async_set_native_value(50.7)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] == 50
        assert isinstance(payload["params"]["cfgTest"], int)

    async def test_nested_params(self, mock_coordinator):
        """Test nested parameter structures like backup reserve level."""
        number = _make_number(
            mock_coordinator,
            param_key="cfgBackupReserve",
            nested_params={"minDsgSoc": None, "maxChgSoc": 100},
        )
        await number.async_set_native_value(30)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgBackupReserve"] == {
            "minDsgSoc": 30,
            "maxChgSoc": 100,
        }

    async def test_set_refreshes_coordinator(self, mock_coordinator):
        number = _make_number(mock_coordinator)
        await number.async_set_native_value(50)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_command_uses_pro_v2_format(self, mock_coordinator):
        number = _make_number(mock_coordinator)
        await number.async_set_native_value(50)
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert "cmdId" in payload
        assert payload["cmdId"] == 17


class TestNumberAttributes:
    """Test number attribute initialization."""

    def test_min_max_step(self, mock_coordinator):
        number = _make_number(mock_coordinator, min_value=10, max_value=90, step=5)
        assert number.native_min_value == 10
        assert number.native_max_value == 90
        assert number.native_step == 5

    def test_unit(self, mock_coordinator):
        number = _make_number(mock_coordinator, unit="%")
        assert number.native_unit_of_measurement == "%"

    def test_icon(self, mock_coordinator):
        number = _make_number(mock_coordinator, icon="mdi:battery")
        assert number.icon == "mdi:battery"

    def test_unique_id(self, mock_coordinator):
        number = _make_number(mock_coordinator, key="max_charge")
        assert number.unique_id == "TEST1234567890_max_charge"

    def test_ac_charge_power_uses_config_step(self, mock_coordinator):
        """Test that ac_charge_power uses configurable step from entry options."""
        entry = MagicMock()
        entry.options = {"power_step": 50}
        number = _make_number(
            mock_coordinator,
            entry=entry,
            key="ac_charge_power",
            step=100,
        )
        assert number.native_step == 50
