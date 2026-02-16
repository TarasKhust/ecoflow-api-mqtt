"""Stream Ultra X sensor definitions."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower

from ..base import EcoFlowSensorDef

SENSORS = [
    EcoFlowSensorDef(
        key="battery_level",
        name="Battery Level",
        state_key="cmsBattSoc",
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    EcoFlowSensorDef(
        key="backup_reserve_level",
        name="Backup Reserve Level",
        state_key="backupReverseSoc",
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart",
    ),
    EcoFlowSensorDef(
        key="max_charge_level",
        name="Max Charge Level",
        state_key="cmsMaxChgSoc",
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-100",
    ),
    EcoFlowSensorDef(
        key="min_discharge_level",
        name="Min Discharge Level",
        state_key="cmsMinDsgSoc",
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-low",
    ),
    EcoFlowSensorDef(
        key="solar_power",
        name="Solar Input Power",
        state_key="powGetPvSum",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    EcoFlowSensorDef(
        key="system_load_power",
        name="System Load Power",
        state_key="powGetSysLoad",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
    ),
    EcoFlowSensorDef(
        key="grid_power",
        name="Grid Power",
        state_key="powGetSysGrid",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    EcoFlowSensorDef(
        key="grid_connection_power",
        name="Grid Connection Power",
        state_key="gridConnectionPower",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    EcoFlowSensorDef(
        key="battery_power",
        name="Battery Power",
        state_key="powGetBpCms",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-sync",
    ),
    EcoFlowSensorDef(
        key="feed_in_mode",
        name="Feed-in Control",
        state_key="feedGridMode",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:transmission-tower-export",
        options=["off", "on"],
    ),
    EcoFlowSensorDef(
        key="last_update",
        name="Last Update",
        state_key="quota_cloud_ts",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
]
