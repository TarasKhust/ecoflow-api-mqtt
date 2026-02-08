"""Number platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_POWER_STEP,
    DEVICE_TYPE_DELTA_2,
    DEVICE_TYPE_DELTA_3_PLUS,
    DEVICE_TYPE_DELTA_PRO,
    DEVICE_TYPE_DELTA_PRO_3,
    DEVICE_TYPE_STREAM_ULTRA_X,
    DOMAIN,
    OPTS_POWER_STEP,
)
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
    # Note: AC Always On Min SOC (acAlwaysOnMiniSoc) is read-only
    # No documented SET command available in EcoFlow API
}

# Number definitions for Delta Pro (Original) based on API documentation
DELTA_PRO_NUMBER_DEFINITIONS = {
    "max_charge_level": {
        "name": "Max Charge Level",
        "state_key": "ems.maxChargeSoc",
        "cmd_set": 32,
        "cmd_id": 49,
        "param_key": "maxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging-100",
        "mode": NumberMode.SLIDER,
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "state_key": "ems.minDsgSoc",
        "cmd_set": 32,
        "cmd_id": 51,
        "param_key": "minDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-10",
        "mode": NumberMode.SLIDER,
    },
    "car_input_current": {
        "name": "Car Input Current",
        "state_key": "mppt.cfgDcChgCurrent",
        "cmd_set": 32,
        "cmd_id": 71,
        "param_key": "currMa",
        "min": 4000,
        "max": 8000,
        "step": 1000,
        "unit": "mA",
        "icon": "mdi:car-battery",
        "mode": NumberMode.SLIDER,
    },
    "screen_brightness": {
        "name": "Screen Brightness",
        "state_key": "pd.lcdBrightness",
        "cmd_set": 32,
        "cmd_id": 39,
        "param_key": "lcdBrightness",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit": PERCENTAGE,
        "icon": "mdi:brightness-6",
        "mode": NumberMode.SLIDER,
    },
    "device_standby_time": {
        "name": "Device Standby Time",
        "state_key": "pd.standByMode",
        "cmd_set": 32,
        "cmd_id": 33,
        "param_key": "standByMode",
        "min": 0,
        "max": 5999,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer-sleep",
        "mode": NumberMode.BOX,
    },
    "screen_timeout": {
        "name": "Screen Timeout",
        "state_key": "pd.lcdOffSec",
        "cmd_set": 32,
        "cmd_id": 39,
        "param_key": "lcdTime",
        "min": 0,
        "max": 1800,
        "step": 30,
        "unit": UnitOfTime.SECONDS,
        "icon": "mdi:monitor-off",
        "mode": NumberMode.BOX,
    },
    "ac_standby_time": {
        "name": "AC Standby Time",
        "state_key": "inv.cfgStandbyMin",
        "cmd_set": 32,
        "cmd_id": 153,
        "param_key": "standByMins",
        "min": 0,
        "max": 720,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
        "mode": NumberMode.BOX,
    },
    "ac_charging_power": {
        "name": "AC Charging Power",
        "state_key": "inv.cfgSlowChgWatts",
        "cmd_set": 32,
        "cmd_id": 69,
        "param_key": "slowChgPower",
        "min": 200,
        "max": 2900,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:lightning-bolt",
        "mode": NumberMode.SLIDER,
    },
    "generator_auto_start_soc": {
        "name": "Generator Auto Start SOC",
        "state_key": "ems.minOpenOilEbSoc",
        "cmd_set": 32,
        "cmd_id": 52,
        "param_key": "openOilSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine",
        "mode": NumberMode.SLIDER,
    },
    "generator_auto_stop_soc": {
        "name": "Generator Auto Stop SOC",
        "state_key": "ems.maxCloseOilEbSoc",
        "cmd_set": 32,
        "cmd_id": 53,
        "param_key": "closeOilSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine-off",
        "mode": NumberMode.SLIDER,
    },
}

# NOTE: River 3 and River 3 Plus are NOT supported by EcoFlow REST API
# These devices return error 1006. Removed from codebase.

# Number definitions for Delta 3 Plus based on API documentation
# Uses Delta Pro 3 API format (cmdId: 17, cmdFunc: 254)
DELTA_3_PLUS_NUMBER_DEFINITIONS = {
    "max_charge_level": {
        "name": "Charge Limit",
        "state_key": "cmsMaxChgSoc",
        "command_key": "cmsMaxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging-100",
        "mode": NumberMode.SLIDER,
    },
    "min_discharge_level": {
        "name": "Discharge Limit",
        "state_key": "cmsMinDsgSoc",
        "command_key": "cmsMinDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-10",
        "mode": NumberMode.SLIDER,
    },
    "ac_charging_power": {
        "name": "AC Charging Power",
        "state_key": "plugInInfoAcInChgPowMax",
        "command_key": "plugInInfoAcInChgPowMax",
        "min": 100,
        "max": 1500,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:lightning-bolt",
        "mode": NumberMode.SLIDER,
    },
    "device_standby_time": {
        "name": "Device Standby Time",
        "state_key": "devStandbyTime",
        "command_key": "devStandbyTime",
        "min": 0,
        "max": 1440,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer-sleep",
        "mode": NumberMode.BOX,
    },
    "screen_timeout": {
        "name": "Screen Timeout",
        "state_key": "screenOffTime",
        "command_key": "screenOffTime",
        "min": 0,
        "max": 1800,
        "step": 30,
        "unit": UnitOfTime.SECONDS,
        "icon": "mdi:monitor-off",
        "mode": NumberMode.BOX,
    },
    "ac_standby_time": {
        "name": "AC Standby Time",
        "state_key": "acStandbyTime",
        "command_key": "acStandbyTime",
        "min": 0,
        "max": 1440,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
        "mode": NumberMode.BOX,
    },
    "dc_standby_time": {
        "name": "DC Standby Time",
        "state_key": "dcStandbyTime",
        "command_key": "dcStandbyTime",
        "min": 0,
        "max": 1440,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
        "mode": NumberMode.BOX,
    },
    "lcd_brightness": {
        "name": "LCD Brightness",
        "state_key": "lcdLight",
        "command_key": "lcdLight",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit": PERCENTAGE,
        "icon": "mdi:brightness-6",
        "mode": NumberMode.SLIDER,
    },
    "generator_start_soc": {
        "name": "Generator Start SOC",
        "state_key": "cmsOilOnSoc",
        "command_key": "cmsOilOnSoc",
        "min": 10,
        "max": 30,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine",
        "mode": NumberMode.SLIDER,
    },
    "generator_stop_soc": {
        "name": "Generator Stop SOC",
        "state_key": "cmsOilOffSoc",
        "command_key": "cmsOilOffSoc",
        "min": 50,
        "max": 100,
        "step": 5,
        "unit": PERCENTAGE,
        "icon": "mdi:engine-off",
        "mode": NumberMode.SLIDER,
    },
}

# Number definitions for Delta 2 based on API documentation
# Uses unique API format with moduleType and operateType parameters
DELTA_2_NUMBER_DEFINITIONS = {
    "max_charge_level": {
        "name": "Max Charge Level",
        "state_key": "bms_emsStatus.maxChargeSoc",
        "module_type": 2,  # BMS
        "operate_type": "upsConfig",
        "param_key": "maxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging-100",
        "mode": NumberMode.SLIDER,
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "state_key": "bms_emsStatus.minDsgSoc",
        "module_type": 2,  # BMS
        "operate_type": "dsgCfg",
        "param_key": "minDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-10",
        "mode": NumberMode.SLIDER,
    },
    "ac_charging_power": {
        "name": "AC Charging Power",
        "state_key": "mppt.cfgChgWatts",
        "module_type": 5,  # MPPT
        "operate_type": "acChgCfg",
        "param_key": "chgWatts",
        "min": 100,
        "max": 1200,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "icon": "mdi:lightning-bolt",
        "mode": NumberMode.SLIDER,
    },
    "device_standby_time": {
        "name": "Device Standby Time",
        "state_key": "pd.standbyMin",
        "module_type": 1,  # PD
        "operate_type": "standbyTime",
        "param_key": "standbyMin",
        "min": 0,
        "max": 720,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer-sleep",
        "mode": NumberMode.BOX,
    },
    "screen_timeout": {
        "name": "Screen Timeout",
        "state_key": "pd.lcdOffSec",
        "module_type": 1,  # PD
        "operate_type": "lcdCfg",
        "param_key": "delayOff",
        "min": 0,
        "max": 1800,
        "step": 30,
        "unit": UnitOfTime.SECONDS,
        "icon": "mdi:monitor-off",
        "mode": NumberMode.BOX,
    },
    "screen_brightness": {
        "name": "Screen Brightness",
        "state_key": "pd.brightLevel",
        "module_type": 1,  # PD
        "operate_type": "lcdCfg",
        "param_key": "brighLevel",
        "min": 0,
        "max": 3,
        "step": 1,
        "unit": None,  # Level 0-3
        "icon": "mdi:brightness-6",
        "mode": NumberMode.SLIDER,
    },
    "dc_charging_current": {
        "name": "DC Charging Current",
        "state_key": "mppt.dcChgCurrent",
        "module_type": 5,  # MPPT
        "operate_type": "dcChgCfg",
        "param_key": "dcChgCfg",
        "min": 4000,
        "max": 10000,
        "step": 1000,
        "unit": "mA",
        "icon": "mdi:current-dc",
        "mode": NumberMode.SLIDER,
    },
    "ac_standby_time": {
        "name": "AC Standby Time",
        "state_key": "mppt.acStandbyMins",
        "module_type": 5,  # MPPT
        "operate_type": "standbyTime",
        "param_key": "standbyMins",
        "min": 0,
        "max": 720,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:timer",
        "mode": NumberMode.BOX,
    },
    "car_standby_time": {
        "name": "Car Charger Standby Time",
        "state_key": "mppt.carStandbyMin",
        "module_type": 5,  # MPPT
        "operate_type": "carStandby",
        "param_key": "standbyMins",
        "min": 0,
        "max": 720,
        "step": 30,
        "unit": UnitOfTime.MINUTES,
        "icon": "mdi:car-clock",
        "mode": NumberMode.BOX,
    },
}

# ============================================================================
# STREAM ULTRA X - Number Definitions
# Based on EcoFlow Developer API documentation for STREAM system
# ============================================================================

STREAM_ULTRA_X_NUMBER_DEFINITIONS = {
    "backup_reserve_level": {
        "name": "Backup Reserve Level",
        "state_key": "backupReverseSoc",
        "param_key": "cfgBackupReverseSoc",
        "min": 3,
        "max": 95,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-heart",
        "mode": NumberMode.SLIDER,
    },
    "max_charge_level": {
        "name": "Max Charge Level",
        "state_key": "cmsMaxChgSoc",
        "param_key": "cfgMaxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-charging-100",
        "mode": NumberMode.SLIDER,
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "state_key": "cmsMinDsgSoc",
        "param_key": "cfgMinDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": PERCENTAGE,
        "icon": "mdi:battery-low",
        "mode": NumberMode.SLIDER,
    },
}


# Map device types to number definitions
DEVICE_NUMBER_MAP = {
    DEVICE_TYPE_DELTA_PRO_3: DELTA_PRO_3_NUMBER_DEFINITIONS,
    DEVICE_TYPE_DELTA_PRO: DELTA_PRO_NUMBER_DEFINITIONS,
    DEVICE_TYPE_DELTA_3_PLUS: DELTA_3_PLUS_NUMBER_DEFINITIONS,
    DEVICE_TYPE_DELTA_2: DELTA_2_NUMBER_DEFINITIONS,
    DEVICE_TYPE_STREAM_ULTRA_X: STREAM_ULTRA_X_NUMBER_DEFINITIONS,
    "delta_pro_3": DELTA_PRO_3_NUMBER_DEFINITIONS,
    "delta_pro": DELTA_PRO_NUMBER_DEFINITIONS,
    "delta_3_plus": DELTA_3_PLUS_NUMBER_DEFINITIONS,
    "delta_2": DELTA_2_NUMBER_DEFINITIONS,
    "stream_ultra_x": STREAM_ULTRA_X_NUMBER_DEFINITIONS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device_type

    # Get number definitions for this device type
    number_definitions = DEVICE_NUMBER_MAP.get(
        device_type, DELTA_PRO_3_NUMBER_DEFINITIONS
    )

    entities: list[NumberEntity] = []

    # Check device type for proper class selection
    is_delta_pro = device_type in (DEVICE_TYPE_DELTA_PRO, "delta_pro")
    is_delta_2 = device_type in (DEVICE_TYPE_DELTA_2, "delta_2")
    is_stream = device_type in (DEVICE_TYPE_STREAM_ULTRA_X, "stream_ultra_x")

    for number_key, number_def in number_definitions.items():
        if is_delta_pro:
            entities.append(
                EcoFlowDeltaProNumber(
                    coordinator=coordinator,
                    entry=entry,
                    number_key=number_key,
                    number_def=number_def,
                )
            )
        elif is_delta_2:
            entities.append(
                EcoFlowDelta2Number(
                    coordinator=coordinator,
                    entry=entry,
                    number_key=number_key,
                    number_def=number_def,
                )
            )
        elif is_stream:
            entities.append(
                EcoFlowStreamNumber(
                    coordinator=coordinator,
                    entry=entry,
                    number_key=number_key,
                    number_def=number_def,
                )
            )
        else:
            entities.append(
                EcoFlowNumber(
                    coordinator=coordinator,
                    entry=entry,
                    number_key=number_key,
                    number_def=number_def,
                )
            )

    async_add_entities(entities)
    _LOGGER.info(
        "Added %d number entities for device type %s", len(entities), device_type
    )


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
        self._attr_has_entity_name = True
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
                command_key: {"energyBackupStartSoc": int_value, "energyBackupEn": True}
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
                "Failed to set %s to %s: %s", self._number_key, int_value, err
            )
            raise


class EcoFlowDeltaProNumber(EcoFlowBaseEntity, NumberEntity):
    """Representation of an EcoFlow Delta Pro number entity.

    Uses the Delta Pro API format with cmdSet and id parameters.
    """

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
        self._attr_has_entity_name = True
        self._attr_translation_key = number_key

        # Set number attributes from config
        self._attr_native_min_value = number_def["min"]
        self._attr_native_max_value = number_def["max"]
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
        """Set new value using Delta Pro API format."""
        device_sn = self.coordinator.device_sn
        cmd_set = self._number_def["cmd_set"]
        cmd_id = self._number_def["cmd_id"]
        param_key = self._number_def["param_key"]

        # Convert to int for API
        int_value = int(value)

        # Build command payload according to Delta Pro API format
        payload = {
            "sn": device_sn,
            "params": {
                "cmdSet": cmd_set,
                "id": cmd_id,
                param_key: int_value,
            },
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
                "Failed to set %s to %s: %s", self._number_key, int_value, err
            )
            raise


class EcoFlowDelta2Number(EcoFlowBaseEntity, NumberEntity):
    """Representation of an EcoFlow Delta 2 number entity.

    Uses the Delta 2 API format with moduleType and operateType parameters.
    """

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
        self._attr_has_entity_name = True
        self._attr_translation_key = number_key

        # Set number attributes from config
        self._attr_native_min_value = number_def["min"]
        self._attr_native_max_value = number_def["max"]
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
        """Set new value using Delta 2 API format."""
        device_sn = self.coordinator.device_sn
        module_type = self._number_def["module_type"]
        operate_type = self._number_def["operate_type"]
        param_key = self._number_def["param_key"]

        # Convert to int for API
        int_value = int(value)

        # Build command payload according to Delta 2 API format
        payload = {
            "id": int(time.time() * 1000),
            "version": "1.0",
            "sn": device_sn,
            "moduleType": module_type,
            "operateType": operate_type,
            "params": {param_key: int_value},
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
                "Failed to set %s to %s: %s", self._number_key, int_value, err
            )
            raise


class EcoFlowStreamNumber(EcoFlowBaseEntity, NumberEntity):
    """Representation of an EcoFlow Stream number entity.

    Uses the Stream API format with cmdId, cmdFunc, dirDest, dirSrc, dest parameters.
    Supported devices: STREAM Ultra, STREAM Pro, STREAM AC Pro, STREAM Ultra X,
                      STREAM Ultra (US), STREAM Max
    """

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
        self._attr_has_entity_name = True
        self._attr_translation_key = number_key

        # Set number attributes from config
        self._attr_native_min_value = number_def["min"]
        self._attr_native_max_value = number_def["max"]
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
        """Set new value using Stream API format."""
        device_sn = self.coordinator.device_sn
        param_key = self._number_def["param_key"]

        # Convert to int for API
        int_value = int(value)

        # Build command payload according to Stream API format
        payload = {
            "sn": device_sn,
            "cmdId": 17,
            "cmdFunc": 254,
            "dirDest": 1,
            "dirSrc": 1,
            "dest": 2,
            "needAck": True,
            "params": {param_key: int_value},
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
                "Failed to set %s to %s: %s", self._number_key, int_value, err
            )
            raise
