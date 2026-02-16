"""Sensor definitions for EcoFlow Smart Plug S401."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from ..base import EcoFlowSensorDef

SENSORS: list[EcoFlowSensorDef] = [
    EcoFlowSensorDef(
        key="power",
        name="Power",
        state_key="2_1.watts",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EcoFlowSensorDef(
        key="voltage",
        name="Voltage",
        state_key="2_1.volt",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EcoFlowSensorDef(
        key="current",
        name="Current",
        state_key="2_1.current",
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EcoFlowSensorDef(
        key="temperature",
        name="Temperature",
        state_key="2_1.temp",
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EcoFlowSensorDef(
        key="frequency",
        name="Frequency",
        state_key="2_1.freq",
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EcoFlowSensorDef(
        key="led_brightness",
        name="LED Brightness",
        state_key="2_1.brightness",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:brightness-6",
    ),
    EcoFlowSensorDef(
        key="max_current",
        name="Maximum Current",
        state_key="2_1.maxCur",
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    EcoFlowSensorDef(
        key="overload_protection_threshold",
        name="Overload Protection Threshold",
        state_key="2_1.maxWatts",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shield-alert",
    ),
    EcoFlowSensorDef(
        key="error_code",
        name="Error Code",
        state_key="2_1.errCode",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EcoFlowSensorDef(
        key="warning_code",
        name="Warning Code",
        state_key="2_1.warnCode",
        icon="mdi:alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EcoFlowSensorDef(
        key="last_update",
        name="Last Update",
        state_key="2_1.updateTime",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]
