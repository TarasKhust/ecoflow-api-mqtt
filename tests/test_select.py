"""Tests for select platform entity logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.ecoflow_api.commands.base import CommandFormat
from custom_components.ecoflow_api.devices.base import EcoFlowSelectDef
from custom_components.ecoflow_api.select import EcoFlowSelect


def _make_select(
    coordinator,
    *,
    key="test_select",
    param_key="cfgTest",
    options=None,
    state_key="testState",
    command_params=None,
    is_local=False,
    nested_params=False,
    cmd_format=CommandFormat.PRO_V2,
):
    """Helper to create an EcoFlowSelect with a definition."""
    if options is None:
        options = {"Option A": 1, "Option B": 2, "Option C": 3}

    defn = EcoFlowSelectDef(
        key=key,
        name="Test Select",
        param_key=param_key,
        options=options,
        state_key=state_key,
        command_params=command_params or {},
        is_local=is_local,
        nested_params=nested_params,
    )
    return EcoFlowSelect(coordinator, defn, cmd_format)


class TestSelectCurrentOption:
    """Test current_option property."""

    def test_value_maps_to_option(self, mock_coordinator):
        mock_coordinator.data = {"testState": 2}
        select = _make_select(mock_coordinator)
        assert select.current_option == "Option B"

    def test_value_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        select = _make_select(mock_coordinator)
        assert select.current_option == "Option A"

    def test_unknown_value(self, mock_coordinator):
        mock_coordinator.data = {"testState": 99}
        select = _make_select(mock_coordinator)
        assert select.current_option is None

    def test_none_data(self, mock_coordinator):
        mock_coordinator.data = None
        select = _make_select(mock_coordinator)
        assert select.current_option is None

    def test_missing_key(self, mock_coordinator):
        mock_coordinator.data = {"other": 1}
        select = _make_select(mock_coordinator)
        assert select.current_option is None


class TestSelectLocalSettings:
    """Test local-only select behavior (update interval)."""

    def test_update_interval_current(self, mock_coordinator):
        mock_coordinator.update_interval_seconds = 15
        select = _make_select(
            mock_coordinator,
            key="update_interval",
            options={
                "5 seconds": 5,
                "15 seconds": 15,
                "30 seconds": 30,
            },
            is_local=True,
        )
        assert select.current_option == "15 seconds"

    def test_update_interval_unknown(self, mock_coordinator):
        mock_coordinator.update_interval_seconds = 99
        select = _make_select(
            mock_coordinator,
            key="update_interval",
            options={"5 seconds": 5, "15 seconds": 15},
            is_local=True,
        )
        assert select.current_option is None


class TestSelectOptionSelection:
    """Test async_select_option."""

    async def test_select_option_sends_command(self, mock_coordinator):
        select = _make_select(mock_coordinator)
        await select.async_select_option("Option B")
        mock_coordinator.async_send_command.assert_called_once()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] == 2

    async def test_invalid_option_logged(self, mock_coordinator):
        select = _make_select(mock_coordinator)
        await select.async_select_option("Nonexistent")
        mock_coordinator.async_send_command.assert_not_called()

    async def test_local_update_interval(self, mock_coordinator):
        select = _make_select(
            mock_coordinator,
            key="update_interval",
            options={"5 seconds": 5, "15 seconds": 15, "30 seconds": 30},
            is_local=True,
        )
        # Mock async_write_ha_state since no real HA instance
        select.async_write_ha_state = MagicMock()
        await select.async_select_option("30 seconds")
        mock_coordinator.async_set_update_interval.assert_called_once_with(30)
        mock_coordinator.async_send_command.assert_not_called()

    async def test_select_refreshes_coordinator(self, mock_coordinator):
        select = _make_select(mock_coordinator)
        await select.async_select_option("Option A")
        mock_coordinator.async_request_refresh.assert_called_once()


class TestSelectAttributes:
    """Test select attribute initialization."""

    def test_options_list(self, mock_coordinator):
        select = _make_select(mock_coordinator)
        assert select.options == ["Option A", "Option B", "Option C"]

    def test_unique_id(self, mock_coordinator):
        select = _make_select(mock_coordinator, key="ac_mode")
        assert select.unique_id == "test_entry_id_123_ac_mode"

    def test_name(self, mock_coordinator):
        select = _make_select(mock_coordinator)
        assert select.name == "Test Select"
