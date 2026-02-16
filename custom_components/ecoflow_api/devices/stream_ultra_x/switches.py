"""Stream Ultra X switch definitions."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass

from ..base import EcoFlowSwitchDef

SWITCHES = [
    EcoFlowSwitchDef(
        key="ac1_output",
        name="AC1 Output",
        state_key="relay2Onoff",
        param_key="cfgRelay2Onoff",
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
        device_class=SwitchDeviceClass.OUTLET,
    ),
    EcoFlowSwitchDef(
        key="ac2_output",
        name="AC2 Output",
        state_key="relay3Onoff",
        param_key="cfgRelay3Onoff",
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
        device_class=SwitchDeviceClass.OUTLET,
    ),
    EcoFlowSwitchDef(
        key="feed_in_control",
        name="Feed-in Control",
        state_key="feedGridMode",
        param_key="cfgFeedGridMode",
        icon_on="mdi:transmission-tower-export",
        icon_off="mdi:transmission-tower-off",
        device_class=SwitchDeviceClass.SWITCH,
        value_on=2,
        value_off=1,
    ),
]
