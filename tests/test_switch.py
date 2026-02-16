"""Tests for switch platform entity logic."""

from __future__ import annotations

from custom_components.ecoflow_api.commands.base import CommandFormat
from custom_components.ecoflow_api.devices.base import EcoFlowSwitchDef
from custom_components.ecoflow_api.switch import EcoFlowSwitch


def _make_switch(
    coordinator,
    *,
    key="test_switch",
    state_key="testState",
    param_key="cfgTest",
    state_interpreter="bool",
    value_on=True,
    value_off=False,
    inverted=False,
    command_params=None,
    icon_on="mdi:power",
    icon_off="mdi:power-off",
):
    """Helper to create an EcoFlowSwitch with a definition."""
    defn = EcoFlowSwitchDef(
        key=key,
        name="Test Switch",
        state_key=state_key,
        param_key=param_key,
        state_interpreter=state_interpreter,
        value_on=value_on,
        value_off=value_off,
        inverted=inverted,
        command_params=command_params or {},
        icon_on=icon_on,
        icon_off=icon_off,
    )
    return EcoFlowSwitch(coordinator, defn, CommandFormat.PRO_V2)


class TestSwitchStateInterpretation:
    """Test is_on property with different state interpreters."""

    # --- bool interpreter (default) ---

    def test_bool_true(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is True

    def test_bool_false(self, mock_coordinator):
        mock_coordinator.data = {"testState": False}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is False

    def test_bool_int_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is True

    def test_bool_int_0(self, mock_coordinator):
        mock_coordinator.data = {"testState": 0}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is False

    def test_bool_string_true(self, mock_coordinator):
        mock_coordinator.data = {"testState": "true"}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is True

    def test_bool_string_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": "1"}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is True

    def test_bool_string_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": "on"}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is True

    def test_bool_string_0(self, mock_coordinator):
        mock_coordinator.data = {"testState": "0"}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is False

    # --- int01 interpreter ---

    def test_int01_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        switch = _make_switch(mock_coordinator, state_interpreter="int01")
        assert switch.is_on is True

    def test_int01_off(self, mock_coordinator):
        mock_coordinator.data = {"testState": 0}
        switch = _make_switch(mock_coordinator, state_interpreter="int01")
        assert switch.is_on is False

    def test_int01_float_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1.0}
        switch = _make_switch(mock_coordinator, state_interpreter="int01")
        assert switch.is_on is True

    def test_int01_string_1(self, mock_coordinator):
        mock_coordinator.data = {"testState": "1"}
        switch = _make_switch(mock_coordinator, state_interpreter="int01")
        assert switch.is_on is True

    # --- flow_info interpreter ---

    def test_flow_info_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": 2}
        switch = _make_switch(mock_coordinator, state_interpreter="flow_info")
        assert switch.is_on is True

    def test_flow_info_off(self, mock_coordinator):
        mock_coordinator.data = {"testState": 0}
        switch = _make_switch(mock_coordinator, state_interpreter="flow_info")
        assert switch.is_on is False

    def test_flow_info_other_value(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        switch = _make_switch(mock_coordinator, state_interpreter="flow_info")
        assert switch.is_on is False

    # --- Custom value_on/value_off ---

    def test_custom_value_on(self, mock_coordinator):
        """Test custom value_on/value_off (e.g., feed_in_control: 1=off, 2=on)."""
        mock_coordinator.data = {"testState": 2}
        switch = _make_switch(mock_coordinator, value_on=2, value_off=1)
        assert switch.is_on is True

    def test_custom_value_off(self, mock_coordinator):
        mock_coordinator.data = {"testState": 1}
        switch = _make_switch(mock_coordinator, value_on=2, value_off=1)
        assert switch.is_on is False

    # --- None / missing state ---

    def test_none_data(self, mock_coordinator):
        mock_coordinator.data = None
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is None

    def test_missing_key(self, mock_coordinator):
        mock_coordinator.data = {"otherKey": True}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is None

    def test_none_value(self, mock_coordinator):
        mock_coordinator.data = {"testState": None}
        switch = _make_switch(mock_coordinator)
        assert switch.is_on is None


class TestSwitchInverted:
    """Test inverted switch behavior."""

    def test_inverted_true_becomes_false(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        switch = _make_switch(mock_coordinator, inverted=True)
        assert switch.is_on is False

    def test_inverted_false_becomes_true(self, mock_coordinator):
        mock_coordinator.data = {"testState": False}
        switch = _make_switch(mock_coordinator, inverted=True)
        assert switch.is_on is True

    def test_inverted_none_stays_none(self, mock_coordinator):
        mock_coordinator.data = {"testState": None}
        switch = _make_switch(mock_coordinator, inverted=True)
        assert switch.is_on is None


class TestSwitchIcon:
    """Test icon property."""

    def test_icon_on(self, mock_coordinator):
        mock_coordinator.data = {"testState": True}
        switch = _make_switch(mock_coordinator, icon_on="mdi:on", icon_off="mdi:off")
        assert switch.icon == "mdi:on"

    def test_icon_off(self, mock_coordinator):
        mock_coordinator.data = {"testState": False}
        switch = _make_switch(mock_coordinator, icon_on="mdi:on", icon_off="mdi:off")
        assert switch.icon == "mdi:off"


class TestSwitchCommands:
    """Test turn_on/turn_off command building."""

    async def test_turn_on_sends_value_on(self, mock_coordinator):
        switch = _make_switch(mock_coordinator)
        await switch.async_turn_on()
        mock_coordinator.async_send_command.assert_called_once()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] is True

    async def test_turn_off_sends_value_off(self, mock_coordinator):
        switch = _make_switch(mock_coordinator)
        await switch.async_turn_off()
        mock_coordinator.async_send_command.assert_called_once()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] is False

    async def test_inverted_turn_on_sends_value_off(self, mock_coordinator):
        switch = _make_switch(mock_coordinator, inverted=True)
        await switch.async_turn_on()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] is False

    async def test_inverted_turn_off_sends_value_on(self, mock_coordinator):
        switch = _make_switch(mock_coordinator, inverted=True)
        await switch.async_turn_off()
        payload = mock_coordinator.async_send_command.call_args[0][0]
        assert payload["params"]["cfgTest"] is True

    async def test_command_includes_format_params(self, mock_coordinator):
        switch = _make_switch(
            mock_coordinator,
            command_params={"cmd_set": 32, "cmd_id": 66},
        )
        # Using PRO_V2 format, extra kwargs are ignored by ProV2CommandBuilder
        # but still passed through build_command
        await switch.async_turn_on()
        mock_coordinator.async_send_command.assert_called_once()

    async def test_turn_on_refreshes_coordinator(self, mock_coordinator):
        switch = _make_switch(mock_coordinator)
        await switch.async_turn_on()
        mock_coordinator.async_request_refresh.assert_called_once()


class TestSwitchUniqueId:
    """Test unique ID generation."""

    def test_unique_id_format(self, mock_coordinator):
        switch = _make_switch(mock_coordinator, key="ac_out")
        assert switch.unique_id == "TEST1234567890_ac_out"
