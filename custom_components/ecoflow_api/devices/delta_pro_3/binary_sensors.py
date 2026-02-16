"""Delta Pro 3 binary sensor definitions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from ..base import EcoFlowBinarySensorDef

BINARY_SENSORS = [
    EcoFlowBinarySensorDef(
        key="ac_in_connected",
        name="AC Input Connected",
        state_key="acInConnected",
        icon_on="mdi:power-plug",
        icon_off="mdi:power-plug-off",
        derived=True,
        derive_from="powGetAcIn",
        derive_condition=lambda v: v is not None and v > 0,
    ),
    EcoFlowBinarySensorDef(
        key="solar_connected",
        name="Solar Connected",
        state_key="solarConnected",
        icon_on="mdi:solar-power",
        icon_off="mdi:solar-power-variant-outline",
        derived=True,
        derive_from="powGetPvH",
        derive_condition=lambda v: v is not None and v > 0,
    ),
    EcoFlowBinarySensorDef(
        key="is_charging",
        name="Is Charging",
        state_key="isCharging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon_on="mdi:battery-charging",
        icon_off="mdi:battery",
        derived=True,
        derive_from="powInSumW",
        derive_condition=lambda v: v is not None and v > 10,
    ),
    EcoFlowBinarySensorDef(
        key="is_discharging",
        name="Is Discharging",
        state_key="isDischarging",
        icon_on="mdi:battery-arrow-down",
        icon_off="mdi:battery",
        derived=True,
        derive_from="powOutSumW",
        derive_condition=lambda v: v is not None and v > 10,
    ),
    EcoFlowBinarySensorDef(
        key="ac_out_enabled",
        name="AC Output Enabled",
        state_key="acOutState",
        device_class=BinarySensorDeviceClass.POWER,
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
    ),
    EcoFlowBinarySensorDef(
        key="dc_out_enabled",
        name="DC Output Enabled",
        state_key="dcOutState",
        device_class=BinarySensorDeviceClass.POWER,
        icon_on="mdi:current-dc",
        icon_off="mdi:power-off",
    ),
    EcoFlowBinarySensorDef(
        key="battery_low",
        name="Battery Low",
        state_key="batteryLow",
        device_class=BinarySensorDeviceClass.BATTERY,
        icon_on="mdi:battery-alert",
        icon_off="mdi:battery",
        derived=True,
        derive_from="bmsBattSoc",
        derive_condition=lambda v: v is not None and v < 20,
    ),
    EcoFlowBinarySensorDef(
        key="battery_full",
        name="Battery Full",
        state_key="batteryFull",
        icon_on="mdi:battery",
        icon_off="mdi:battery-outline",
        derived=True,
        derive_from="bmsBattSoc",
        derive_condition=lambda v: v is not None and v >= 100,
    ),
    EcoFlowBinarySensorDef(
        key="over_temp",
        name="Over Temperature",
        state_key="overTemp",
        device_class=BinarySensorDeviceClass.HEAT,
        icon_on="mdi:thermometer-alert",
        icon_off="mdi:thermometer",
        derived=True,
        derive_from="bmsMaxCellTemp",
        derive_condition=lambda v: v is not None and v > 45,
    ),
]
