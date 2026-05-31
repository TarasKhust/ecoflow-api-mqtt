"""Constants for River 3 Plus device."""
from __future__ import annotations

from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)

# Device information
DEVICE_TYPE: Final = "River 3 Plus"
DEVICE_MODEL: Final = "River 3 Plus"

# Supported MQTT + Protobuf sensor keys (keep in sync with River3PlusState).
SENSOR_KEYS: Final[tuple[str, ...]] = (
    "battery_level",
    "temperature",
    "ac_in_power",
    "pow_in_sum_w",
    "pow_out_sum_w",
    "temp_pcs_dc",
    "temp_pcs_ac",
    "ac_in_voltage",
    "ac_out_voltage",
    "ac_in_current",
    "ac_out_current",
)


# Home Assistant sensor entity definitions (plain dicts, keyed by entity name).
# Keys map to the decoded River3PlusState fields produced by the protobuf decoder.
RIVER3PLUS_SENSOR_DEFINITIONS = {
    "battery_level": {
        "name": "Battery SOC",
        "key": "battery_level",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "temperature": {
        "name": "Temperature",
        "key": "temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "ac_in_power": {
        "name": "AC Input Power",
        "key": "ac_in_power",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-plug",
    },
    "pow_in_sum_w": {
        "name": "Total Input Power",
        "key": "pow_in_sum_w",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-import",
    },
    "pow_out_sum_w": {
        "name": "Total Output Power",
        "key": "pow_out_sum_w",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-export",
    },
    "temp_pcs_dc": {
        "name": "PCS DC Temperature",
        "key": "temp_pcs_dc",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "temp_pcs_ac": {
        "name": "PCS AC Temperature",
        "key": "temp_pcs_ac",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "ac_in_voltage": {
        "name": "AC Input Voltage",
        "key": "ac_in_voltage",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "ac_out_voltage": {
        "name": "AC Output Voltage",
        "key": "ac_out_voltage",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "ac_in_current": {
        "name": "AC Input Current",
        "key": "ac_in_current",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
    "ac_out_current": {
        "name": "AC Output Current",
        "key": "ac_out_current",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
}
