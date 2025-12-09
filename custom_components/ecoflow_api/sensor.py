"""Sensor platform for EcoFlow API integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Sensor definitions for Delta Pro 3
# Keys are the API response keys, values define the sensor configuration
DELTA_PRO_3_SENSOR_DEFINITIONS = {
    # Battery
    "soc": {
        "name": "Battery Level",
        "key": "soc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "soh": {
        "name": "State of Health",
        "key": "soh",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "cycles": {
        "name": "Cycles",
        "key": "cycles",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-sync",
    },
    "full_cap": {
        "name": "Full Capacity",
        "key": "fullCap",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "remain_cap": {
        "name": "Remaining Capacity",
        "key": "remainCap",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-medium",
    },
    # Power - Input
    "watts_in_sum": {
        "name": "Total In Power",
        "key": "wattsInSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-import",
    },
    "ac_in_power": {
        "name": "AC In Power",
        "key": "acInPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-plug",
    },
    "solar_in_power": {
        "name": "Solar In Power",
        "key": "solarInPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "solar_hv_in_power": {
        "name": "Solar HV In Power",
        "key": "solarHvInPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "solar_lv_in_power": {
        "name": "Solar LV In Power",
        "key": "solarLvInPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    # Power - Output
    "watts_out_sum": {
        "name": "Total Out Power",
        "key": "wattsOutSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-export",
    },
    "ac_out_power": {
        "name": "AC Out Power",
        "key": "acOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "ac_hv_out_power": {
        "name": "AC HV Out Power",
        "key": "acHvOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "ac_lv_out_power": {
        "name": "AC LV Out Power",
        "key": "acLvOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "dc_out_power": {
        "name": "DC Out Power",
        "key": "dcOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "dc12v_out_power": {
        "name": "12V DC Out Power",
        "key": "dc12vOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "dc24v_out_power": {
        "name": "24V DC Out Power",
        "key": "dc24vOutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "usb1_out_power": {
        "name": "USB 1 Out Power",
        "key": "usb1OutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "usb2_out_power": {
        "name": "USB 2 Out Power",
        "key": "usb2OutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "type_c1_out_power": {
        "name": "Type-C 1 Out Power",
        "key": "typeC1OutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "type_c2_out_power": {
        "name": "Type-C 2 Out Power",
        "key": "typeC2OutPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    # Time
    "chg_remain_time": {
        "name": "Charge Remaining Time",
        "key": "chgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "dsg_remain_time": {
        "name": "Discharge Remaining Time",
        "key": "dsgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    # Temperature
    "bms_temp": {
        "name": "Battery Temperature",
        "key": "bmsTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "min_cell_temp": {
        "name": "Min Cell Temperature",
        "key": "minCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "max_cell_temp": {
        "name": "Max Cell Temperature",
        "key": "maxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Voltage
    "bms_vol": {
        "name": "Battery Voltage",
        "key": "bmsVol",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "min_cell_vol": {
        "name": "Min Cell Voltage",
        "key": "minCellVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "max_cell_vol": {
        "name": "Max Cell Voltage",
        "key": "maxCellVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "ac_in_vol": {
        "name": "AC In Voltage",
        "key": "acInVol",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Current
    "bms_cur": {
        "name": "Battery Current",
        "key": "bmsCur",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Energy
    "chg_energy": {
        "name": "Total Charge Energy",
        "key": "chgEnergy",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:transmission-tower-import",
    },
    "dsg_energy": {
        "name": "Total Discharge Energy",
        "key": "dsgEnergy",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:transmission-tower-export",
    },
    # Settings (displayed as sensors)
    "ac_chg_power": {
        "name": "AC Charging Power Setting",
        "key": "acChgPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    "max_chg_soc": {
        "name": "Max Charge Level Setting",
        "key": "maxChgSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-90",
    },
    "min_dsg_soc": {
        "name": "Min Discharge Level Setting",
        "key": "minDsgSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-10",
    },
}

# Extra Battery sensor definitions for Delta Pro 3 Smart Extra Battery
# These can be found in API response with various prefixes: slave1*, bms2*, eb1*, etc.
EXTRA_BATTERY_SENSOR_DEFINITIONS = {
    # Battery Level
    "soc": {
        "name": "Battery Level",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "soh": {
        "name": "State of Health",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "cycles": {
        "name": "Cycles",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-sync",
    },
    "full_cap": {
        "name": "Full Capacity",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "remain_cap": {
        "name": "Remaining Capacity",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-medium",
    },
    # Temperature
    "temp": {
        "name": "Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "min_cell_temp": {
        "name": "Min Cell Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "max_cell_temp": {
        "name": "Max Cell Temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Voltage
    "vol": {
        "name": "Voltage",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "min_cell_vol": {
        "name": "Min Cell Voltage",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "max_cell_vol": {
        "name": "Max Cell Voltage",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Current
    "cur": {
        "name": "Current",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    # Power
    "in_power": {
        "name": "In Power",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "out_power": {
        "name": "Out Power",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
}

# Possible prefixes for extra battery data in API response
EXTRA_BATTERY_PREFIXES = [
    "slave1",      # Common prefix (slave1Soc, slave1Temp)
    "slave2",      # Second extra battery
    "bms2",        # Alternative prefix (bms2Soc, bms2Temp)
    "bms3",        # Third battery
    "eb1",         # Extra battery 1
    "eb2",         # Extra battery 2
    "extraBms",    # Extra BMS prefix
    "slaveBattery",  # Another variant
]

# Key mappings for extra battery (API key suffix -> sensor definition key)
EXTRA_BATTERY_KEY_MAPPINGS = {
    "Soc": "soc",
    "soc": "soc",
    "Soh": "soh",
    "soh": "soh",
    "Cycles": "cycles",
    "cycles": "cycles",
    "FullCap": "fullCap",
    "fullCap": "fullCap",
    "RemainCap": "remainCap",
    "remainCap": "remainCap",
    "Temp": "temp",
    "temp": "temp",
    "MinCellTemp": "minCellTemp",
    "minCellTemp": "minCellTemp",
    "MaxCellTemp": "maxCellTemp",
    "maxCellTemp": "maxCellTemp",
    "Vol": "vol",
    "vol": "vol",
    "MinCellVol": "minCellVol",
    "minCellVol": "minCellVol",
    "MaxCellVol": "maxCellVol",
    "maxCellVol": "maxCellVol",
    "Cur": "cur",
    "cur": "cur",
    "InPower": "inPower",
    "inPower": "inPower",
    "OutPower": "outPower",
    "outPower": "outPower",
}


def _detect_extra_batteries(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Detect extra batteries in API response data.
    
    Args:
        data: API response data
        
    Returns:
        Dictionary mapping battery prefix to found keys
        Example: {"slave1": {"Soc": "slave1Soc", "Temp": "slave1Temp"}}
    """
    if not data:
        return {}
    
    extra_batteries: dict[str, dict[str, str]] = {}
    
    for key in data.keys():
        for prefix in EXTRA_BATTERY_PREFIXES:
            if key.startswith(prefix):
                # Extract the suffix (e.g., "Soc" from "slave1Soc")
                suffix = key[len(prefix):]
                
                # Check if it's a known suffix
                if suffix in EXTRA_BATTERY_KEY_MAPPINGS:
                    if prefix not in extra_batteries:
                        extra_batteries[prefix] = {}
                    extra_batteries[prefix][suffix] = key
    
    return extra_batteries


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensor entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowSensor] = []
    
    # Add main device sensors based on available data
    if coordinator.data:
        for sensor_key, sensor_def in DELTA_PRO_3_SENSOR_DEFINITIONS.items():
            # Check if data key exists (might be nested)
            data_key = sensor_def.get("key", sensor_key)
            if _get_nested_value(coordinator.data, data_key) is not None:
                entities.append(
                    EcoFlowSensor(
                        coordinator=coordinator,
                        sensor_key=sensor_key,
                        sensor_def=sensor_def,
                    )
                )
                _LOGGER.debug("Adding sensor: %s", sensor_def["name"])
        
        # Detect and add extra battery sensors
        extra_batteries = _detect_extra_batteries(coordinator.data)
        _LOGGER.info("Detected %d extra batteries: %s", len(extra_batteries), list(extra_batteries.keys()))
        
        for prefix, found_keys in extra_batteries.items():
            battery_num = _get_battery_number(prefix)
            _LOGGER.debug("Adding sensors for Extra Battery %d (prefix: %s)", battery_num, prefix)
            
            for suffix, api_key in found_keys.items():
                sensor_def_key = EXTRA_BATTERY_KEY_MAPPINGS.get(suffix)
                if sensor_def_key and sensor_def_key in EXTRA_BATTERY_SENSOR_DEFINITIONS:
                    base_def = EXTRA_BATTERY_SENSOR_DEFINITIONS[sensor_def_key].copy()
                    entities.append(
                        EcoFlowExtraBatterySensor(
                            coordinator=coordinator,
                            battery_prefix=prefix,
                            battery_number=battery_num,
                            sensor_suffix=suffix,
                            api_key=api_key,
                            sensor_def=base_def,
                        )
                    )
                    _LOGGER.debug(
                        "Adding Extra Battery %d sensor: %s (key: %s)",
                        battery_num, base_def["name"], api_key
                    )
    else:
        # Add all main sensors if no data yet
        for sensor_key, sensor_def in DELTA_PRO_3_SENSOR_DEFINITIONS.items():
            entities.append(
                EcoFlowSensor(
                    coordinator=coordinator,
                    sensor_key=sensor_key,
                    sensor_def=sensor_def,
                )
            )

    async_add_entities(entities)
    _LOGGER.info("Added %d sensors for %s", len(entities), coordinator.device_sn)


def _get_battery_number(prefix: str) -> int:
    """Extract battery number from prefix.
    
    Args:
        prefix: Battery prefix like "slave1", "bms2", "eb1"
        
    Returns:
        Battery number (1-based)
    """
    # Extract number from prefix
    import re
    match = re.search(r'(\d+)', prefix)
    if match:
        return int(match.group(1))
    return 1


def _get_nested_value(data: dict, key: str) -> Any:
    """Get value from nested dictionary using dot notation.
    
    Args:
        data: Data dictionary
        key: Key with optional dot notation (e.g., "bms.soc")
        
    Returns:
        Value or None if not found
    """
    if not data:
        return None
        
    keys = key.split(".")
    value = data
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return None
            
    return value


class EcoFlowSensor(EcoFlowBaseEntity, SensorEntity):
    """EcoFlow sensor entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        sensor_key: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: Data update coordinator
            sensor_key: Unique key for this sensor
            sensor_def: Sensor definition dictionary
        """
        super().__init__(coordinator, sensor_key)
        
        self._sensor_def = sensor_def
        self._data_key = sensor_def.get("key", sensor_key)
        
        # Set entity attributes from definition
        self._attr_name = sensor_def["name"]
        self._attr_native_unit_of_measurement = sensor_def.get("unit")
        self._attr_device_class = sensor_def.get("device_class")
        self._attr_state_class = sensor_def.get("state_class")
        
        if sensor_def.get("icon"):
            self._attr_icon = sensor_def["icon"]

    @property
    def native_value(self) -> float | int | str | None:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
            
        value = _get_nested_value(self.coordinator.data, self._data_key)
        
        if value is None:
            return None
            
        # Handle special conversions
        if self._data_key in ("bmsVol",) and value:
            # Convert to V if stored in mV
            if value > 1000:
                value = value / 1000
                
        return value


class EcoFlowExtraBatterySensor(EcoFlowBaseEntity, SensorEntity):
    """EcoFlow Extra Battery sensor entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        battery_prefix: str,
        battery_number: int,
        sensor_suffix: str,
        api_key: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the extra battery sensor.
        
        Args:
            coordinator: Data update coordinator
            battery_prefix: Battery prefix (e.g., "slave1")
            battery_number: Battery number (1, 2, etc.)
            sensor_suffix: Sensor suffix (e.g., "Soc")
            api_key: Full API key (e.g., "slave1Soc")
            sensor_def: Sensor definition dictionary
        """
        # Create unique key for this extra battery sensor
        entity_key = f"extra_battery_{battery_number}_{sensor_suffix.lower()}"
        super().__init__(coordinator, entity_key)
        
        self._battery_prefix = battery_prefix
        self._battery_number = battery_number
        self._sensor_suffix = sensor_suffix
        self._api_key = api_key
        self._sensor_def = sensor_def
        
        # Set entity attributes from definition with "Extra Battery X" prefix
        self._attr_name = f"Extra Battery {battery_number} {sensor_def['name']}"
        self._attr_native_unit_of_measurement = sensor_def.get("unit")
        self._attr_device_class = sensor_def.get("device_class")
        self._attr_state_class = sensor_def.get("state_class")
        
        if sensor_def.get("icon"):
            self._attr_icon = sensor_def["icon"]

    @property
    def native_value(self) -> float | int | str | None:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
            
        value = self.coordinator.data.get(self._api_key)
        
        if value is None:
            return None
            
        # Handle voltage conversion if needed
        if self._sensor_suffix.lower() == "vol" and value and value > 1000:
            value = value / 1000
                
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "battery_number": self._battery_number,
            "battery_prefix": self._battery_prefix,
            "api_key": self._api_key,
        }
