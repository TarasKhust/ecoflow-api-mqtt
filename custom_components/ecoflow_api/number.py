"""Number platform for EcoFlow API integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (PERCENTAGE, UnitOfElectricCurrent,
                                 UnitOfPower, UnitOfTime)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_POWER_STEP, DOMAIN, OPTS_POWER_STEP
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Number definitions for Delta Pro 3 based on API documentation
DELTA_PRO_3_NUMBER_DEFINITIONS = {
    "max_charge_level": {
        "name": "Max Charge Level",
        "state_key": "cmsMaxChgSoc",
        "command_key": "cfgMaxChgSoc",
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging-100",
        "mode": NumberMode.SLIDER,
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "state_key": "cmsMinDsgSoc",
        "command_key": "cfgMinDsgSoc",
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-10",
        "mode": NumberMode.SLIDER,
    },
    "ac_charge_power": {
        "name": "AC Charging Power",
        "state_key": "plugInInfoAcInChgPowMax",
        "command_key": "cfgPlugInInfoAcInChgPowMax",
        "min": 200,
        "max": 2900,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:lightning-bolt",
        "mode": NumberMode.SLIDER,
    },
    "lcd_brightness": {
        "name": "LCD Brightness",
        "state_key": "lcdLight",
        "command_key": "cfgLcdLight",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit": PERCENTAGE,
        "icon": "mdi:brightness-6",
        "mode": NumberMode.SLIDER,
    },
    "screen_off_time": {
        "name": "Screen Off Time",
        "state_key": "screenOffTime",
        "command_key": "cfgScreenOffTime",
        "min": 0,
        "max": 3600,
        "step": 30,
        "unit": UnitOfTime.SECONDS,
        "icon": "mdi:monitor-off",
        "mode": NumberMode.BOX,
    },
    "generator_start_soc": {
        "name": "Generator Start SOC",
        "state_key": "cmsOilOnSoc",
        "command_key": "cfgCmsOilOnSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine",
        "mode": NumberMode.SLIDER,
    },
    "generator_stop_soc": {
        "name": "Generator Stop SOC",
        "state_key": "cmsOilOffSoc",
        "command_key": "cfgCmsOilOffSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine-off",
        "mode": NumberMode.SLIDER,
    },
    "pv_lv_max_current": {
        "name": "Solar LV Max Current",
        "state_key": "plugInInfoPvLDcAmpMax",
        "command_key": "cfgPlugInInfoPvLDcAmpMax",
        "min": 0,
        "max": 8,
        "step": 1,
        "unit": UnitOfElectricCurrent.AMPERE,
        "icon": "mdi:current-dc",
        "mode": NumberMode.BOX,
    },
    "pv_hv_max_current": {
        "name": "Solar HV Max Current",
        "state_key": "plugInInfoPvHDcAmpMax",
        "command_key": "cfgPlugInInfoPvHDcAmpMax",
        "min": 0,
        "max": 20,
        "step": 1,
        "unit": UnitOfElectricCurrent.AMPERE,
        "icon": "mdi:current-dc",
        "mode": NumberMode.BOX,
    },
    "power_inout_max_charge": {
        "name": "Power In/Out Max Charge",
        "state_key": "plugInInfo5p8ChgPowMax",
        "command_key": "cfgPlugInInfo5p8ChgPowMax",
        "min": 0,
        "max": 4000,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:battery-charging-high",
        "mode": NumberMode.SLIDER,
    },
    "device_standby_time": {
        "name": "Device Standby Time",
        "state_key": "devStandbyTime",
        "command_key": "cfgDevStandbyTime",
        "min": 0,
        "max": 1440,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
        "mode": NumberMode.BOX,
    },
    "ble_standby_time": {
        "name": "Bluetooth Standby Time",
        "state_key": "bleStandbyTime",
        "command_key": "cfgBleStandbyTime",
        "min": 0,
        "max": 3600,
        "step": 60,
        "unit": UnitOfTime.SECONDS,
        "icon": "mdi:bluetooth",
        "mode": NumberMode.BOX,
    },
    "backup_reserve_level": {
        "name": "Backup Reserve Level",
        "state_key": "backupReverseSoc",
        "command_key": "cfgEnergyBackup",
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-lock",
        "mode": NumberMode.SLIDER,
        "nested_params": True,
    },
    "generator_pv_hybrid_max_soc": {
        "name": "Generator PV Hybrid Max SOC",
        "state_key": "generatorPvHybridModeSocMax",
        "command_key": "cfgGeneratorPvHybridModeSocMax",
        "min": 0,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:solar-power",
        "mode": NumberMode.SLIDER,
    },
    "generator_care_start_time": {
        "name": "Generator Care Start Time",
        "state_key": "generatorCareModeStartTime",
        "command_key": "cfgGeneratorCareModeStartTime",
        "min": 0,
        "max": 1440,
        "step": 1,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:weather-night",
        "mode": NumberMode.BOX,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowNumber] = []
    
    for number_key, number_def in DELTA_PRO_3_NUMBER_DEFINITIONS.items():
        entities.append(
            EcoFlowNumber(
                coordinator=coordinator,
                entry=entry,
                number_key=number_key,
                number_def=number_def,
            )
        )
    
    async_add_entities(entities)
    _LOGGER.info("Added %d number entities", len(entities))


class EcoFlowNumber(EcoFlowBaseEntity, NumberEntity):
    """Representation of an EcoFlow number entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        number_key: str,
        number_def: dict[str, Any],
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, number_key)
        self._number_key = number_key
        self._number_def = number_def
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{number_key}"
        self._attr_name = number_def["name"]
        self._attr_translation_key = number_key
        
        # Set number attributes from config
        self._attr_native_min_value = number_def["min"]
        self._attr_native_max_value = number_def["max"]
        
        # Use power_step from options for AC Charging Power, otherwise use default step
        if number_key == "ac_charge_power":
            power_step = self._entry.options.get(OPTS_POWER_STEP, DEFAULT_POWER_STEP)
            self._attr_native_step = power_step
        else:
            self._attr_native_step = number_def["step"]
        
        self._attr_native_unit_of_measurement = number_def.get("unit")
        self._attr_icon = number_def.get("icon")
        self._attr_mode = number_def.get("mode", NumberMode.AUTO)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None
        
        state_key = self._number_def["state_key"]
        value = self.coordinator.data.get(state_key)
        
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        command_key = self._number_def["command_key"]
        device_sn = self.coordinator.config_entry.data["device_sn"]
        
        # Convert to int for API
        int_value = int(value)
        
        # Handle nested parameters for backup reserve level
        params: dict[str, Any]
        if self._number_def.get("nested_params"):
            # Special case for backup reserve level - needs nested structure
            params = {
                command_key: {
                    "energyBackupStartSoc": int_value,
                    "energyBackupEn": True
                }
            }
        else:
            # Standard simple parameter structure
            params = {command_key: int_value}
        
        # Build command payload according to Delta Pro 3 API format
        payload = {
            "sn": device_sn,
            "cmdId": 17,
            "dirDest": 1,
            "dirSrc": 1,
            "cmdFunc": 254,
            "dest": 2,
            "needAck": True,
            "params": params,
        }
        
        try:
            await self.coordinator.api_client.set_device_quota(
                device_sn=device_sn,
                cmd_code=payload,
            )
            # Wait 2 seconds for device to apply changes, then refresh
            await asyncio.sleep(2)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set %s to %s: %s",
                self._number_key,
                int_value,
                err
            )
            raise
