"""Switch definitions for EcoFlow Smart Plug S401."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass

from ..base import EcoFlowSwitchDef

SWITCHES: list[EcoFlowSwitchDef] = [
    EcoFlowSwitchDef(
        key="outlet",
        name="Outlet",
        state_key="2_1.switchSta",
        param_key="plugSwitch",
        command_params={"cmd_code": "WN511_SOCKET_SET_PLUG_SWITCH_MESSAGE"},
        value_on=1,
        value_off=0,
        icon_on="mdi:power-plug",
        icon_off="mdi:power-plug-off",
        device_class=SwitchDeviceClass.OUTLET,
    ),
]
