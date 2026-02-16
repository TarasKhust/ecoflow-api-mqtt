"""Switch definitions for EcoFlow Delta Pro."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass

from ..base import EcoFlowSwitchDef

SWITCHES: list[EcoFlowSwitchDef] = [
    EcoFlowSwitchDef(
        key="ac_output",
        name="AC Output",
        state_key="inv.cfgAcEnabled",
        param_key="enabled",
        command_params={"cmd_set": 32, "cmd_id": 66},
        value_on=1,
        value_off=0,
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
        device_class=SwitchDeviceClass.OUTLET,
        state_interpreter="int01",
    ),
    EcoFlowSwitchDef(
        key="x_boost",
        name="X-Boost",
        state_key="inv.cfgAcXboost",
        param_key="xboost",
        command_params={"cmd_set": 32, "cmd_id": 66},
        value_on=1,
        value_off=0,
        icon_on="mdi:lightning-bolt",
        icon_off="mdi:lightning-bolt-outline",
        device_class=SwitchDeviceClass.SWITCH,
        state_interpreter="int01",
    ),
    EcoFlowSwitchDef(
        key="car_charger",
        name="Car Charger",
        state_key="mppt.carState",
        param_key="enabled",
        command_params={"cmd_set": 32, "cmd_id": 81},
        value_on=1,
        value_off=0,
        icon_on="mdi:car",
        icon_off="mdi:car-off",
        device_class=SwitchDeviceClass.SWITCH,
        state_interpreter="int01",
    ),
    EcoFlowSwitchDef(
        key="beeper",
        name="Beeper",
        state_key="pd.beepState",
        param_key="enabled",
        command_params={"cmd_set": 32, "cmd_id": 38},
        value_on=1,
        value_off=0,
        icon_on="mdi:volume-high",
        icon_off="mdi:volume-off",
        device_class=SwitchDeviceClass.SWITCH,
        state_interpreter="int01",
    ),
    EcoFlowSwitchDef(
        key="bypass_ac_auto_start",
        name="Bypass AC Auto Start",
        state_key="inv.acPassbyAutoEn",
        param_key="enabled",
        command_params={"cmd_set": 32, "cmd_id": 84},
        value_on=1,
        value_off=0,
        icon_on="mdi:power-plug",
        icon_off="mdi:power-plug-off",
        device_class=SwitchDeviceClass.SWITCH,
        state_interpreter="int01",
    ),
]
