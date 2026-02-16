"""Stream Ultra X binary sensor definitions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from ..base import EcoFlowBinarySensorDef

BINARY_SENSORS = [
    EcoFlowBinarySensorDef(
        key="ac1_switch",
        name="AC1 Switch",
        state_key="relay2Onoff",
        device_class=BinarySensorDeviceClass.POWER,
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
    ),
    EcoFlowBinarySensorDef(
        key="ac2_switch",
        name="AC2 Switch",
        state_key="relay3Onoff",
        device_class=BinarySensorDeviceClass.POWER,
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
    ),
    EcoFlowBinarySensorDef(
        key="self_powered_mode",
        name="Self-Powered Mode",
        state_key="energyStrategyOperateMode.operateSelfPoweredOpen",
        icon_on="mdi:home-battery",
        icon_off="mdi:home-battery-outline",
    ),
    EcoFlowBinarySensorDef(
        key="ai_mode",
        name="AI Mode",
        state_key="energyStrategyOperateMode.operateIntelligentScheduleModeOpen",
        icon_on="mdi:robot",
        icon_off="mdi:robot-outline",
    ),
    EcoFlowBinarySensorDef(
        key="battery_charging",
        name="Battery Charging",
        state_key="powGetBpCms",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon_on="mdi:battery-charging",
        icon_off="mdi:battery",
        derived=True,
        derive_condition=lambda v: v is not None and v > 10,
    ),
    EcoFlowBinarySensorDef(
        key="battery_discharging",
        name="Battery Discharging",
        state_key="powGetBpCms",
        icon_on="mdi:battery-arrow-down",
        icon_off="mdi:battery",
        derived=True,
        derive_condition=lambda v: v is not None and v < -10,
    ),
    EcoFlowBinarySensorDef(
        key="solar_generating",
        name="Solar Generating",
        state_key="powGetPvSum",
        icon_on="mdi:solar-power",
        icon_off="mdi:solar-power-variant-outline",
        derived=True,
        derive_condition=lambda v: v is not None and v > 10,
    ),
    EcoFlowBinarySensorDef(
        key="grid_feed_in",
        name="Grid Feed-in",
        state_key="gridConnectionPower",
        icon_on="mdi:transmission-tower-export",
        icon_off="mdi:transmission-tower",
        derived=True,
        derive_condition=lambda v: v is not None and v < -10,
    ),
    EcoFlowBinarySensorDef(
        key="grid_consuming",
        name="Grid Consuming",
        state_key="gridConnectionPower",
        icon_on="mdi:transmission-tower-import",
        icon_off="mdi:transmission-tower",
        derived=True,
        derive_condition=lambda v: v is not None and v > 10,
    ),
]
