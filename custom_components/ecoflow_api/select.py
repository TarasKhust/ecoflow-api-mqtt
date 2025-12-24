"""Select platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_DELTA_PRO, DEVICE_TYPE_DELTA_PRO_3, DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Select definitions for Delta Pro 3 based on API documentation
DELTA_PRO_3_SELECT_DEFINITIONS = {
    "update_interval": {
        "name": "Update Interval",
        "state_key": None,  # Special: stored in coordinator, not device
        "command_key": None,  # Special: local setting
        "icon": "mdi:update",
        "options": {
            "5 seconds (Fast)": 5,
            "10 seconds": 10,
            "15 seconds (Recommended)": 15,
            "30 seconds": 30,
            "60 seconds (Slow)": 60,
        },
        "is_local": True,  # Mark as local setting
    },
    "ac_standby_time": {
        "name": "AC Standby Time",
        "state_key": "acStandbyTime",
        "command_key": "cfgAcStandbyTime",
        "icon": "mdi:timer",
        "options": {
            "Never": 0,
            "30 min": 30,
            "1 hour": 60,
            "2 hours": 120,
            "4 hours": 240,
            "6 hours": 360,
        },
    },
    "dc_standby_time": {
        "name": "DC Standby Time",
        "state_key": "dcStandbyTime",
        "command_key": "cfgDcStandbyTime",
        "icon": "mdi:timer",
        "options": {
            "Never": 0,
            "30 min": 30,
            "1 hour": 60,
            "2 hours": 120,
            "4 hours": 240,
            "6 hours": 360,
        },
    },
    "battery_charge_mode": {
        "name": "Battery Charge/Discharge Mode",
        "state_key": "multiBpChgDsgMode",
        "command_key": "cfgMultiBpChgDsgMode",
        "icon": "mdi:battery-sync",
        "options": {
            "Default": 0,
            "Auto (by voltage)": 1,
            "Main priority charge, Extra priority discharge": 2,
        },
    },
    "ac_output_frequency": {
        "name": "AC Output Frequency",
        "state_key": "acOutFreq",
        "command_key": "cfgAcOutFreq",
        "icon": "mdi:sine-wave",
        "options": {
            "50 Hz": 50,
            "60 Hz": 60,
        },
    },
    "energy_strategy_mode": {
        "name": "Energy Strategy Mode",
        "state_key": None,  # Special: multiple keys checked
        "command_key": "cfgEnergyStrategyOperateMode",
        "icon": "mdi:lightning-bolt",
        "options": {
            "Off": "off",
            "Self-Powered": "self_powered",
            "TOU": "tou",
        },
        "nested_params": True,
    },
}

# Select definitions for Delta Pro (Original) based on API documentation
DELTA_PRO_SELECT_DEFINITIONS = {
    "update_interval": {
        "name": "Update Interval",
        "state_key": None,  # Special: stored in coordinator, not device
        "command_key": None,  # Special: local setting
        "icon": "mdi:update",
        "options": {
            "5 seconds (Fast)": 5,
            "10 seconds": 10,
            "15 seconds (Recommended)": 15,
            "30 seconds": 30,
            "60 seconds (Slow)": 60,
        },
        "is_local": True,  # Mark as local setting
    },
    "pv_charging_type": {
        "name": "PV Charging Type",
        "state_key": "mppt.cfgChgType",
        "cmd_set": 32,
        "cmd_id": 82,
        "param_key": "chgType",
        "icon": "mdi:solar-power",
        "options": {
            "Auto": 0,
            "MPPT": 1,
            "Adapter": 2,
        },
    },
    "ac_output_frequency": {
        "name": "AC Output Frequency",
        "state_key": "inv.cfgAcOutFreq",
        "cmd_set": 32,
        "cmd_id": 66,
        "param_key": "cfgAcOutFreq",
        "icon": "mdi:sine-wave",
        "options": {
            "50 Hz": 1,
            "60 Hz": 2,
        },
    },
}

# Map device types to select definitions
DEVICE_SELECT_MAP = {
    DEVICE_TYPE_DELTA_PRO_3: DELTA_PRO_3_SELECT_DEFINITIONS,
    DEVICE_TYPE_DELTA_PRO: DELTA_PRO_SELECT_DEFINITIONS,
    "delta_pro_3": DELTA_PRO_3_SELECT_DEFINITIONS,
    "delta_pro": DELTA_PRO_SELECT_DEFINITIONS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow select entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device_type

    # Get select definitions for this device type
    select_definitions = DEVICE_SELECT_MAP.get(
        device_type, DELTA_PRO_3_SELECT_DEFINITIONS
    )

    entities: list[SelectEntity] = []

    # Check if this is a Delta Pro (original) device
    is_delta_pro = device_type in (DEVICE_TYPE_DELTA_PRO, "delta_pro")

    for select_key, select_def in select_definitions.items():
        if is_delta_pro and not select_def.get("is_local"):
            entities.append(
                EcoFlowDeltaProSelect(
                    coordinator=coordinator,
                    entry=entry,
                    select_key=select_key,
                    select_def=select_def,
                )
            )
        else:
            entities.append(
                EcoFlowSelect(
                    coordinator=coordinator,
                    entry=entry,
                    select_key=select_key,
                    select_def=select_def,
                )
            )

    async_add_entities(entities)
    _LOGGER.info(
        "Added %d select entities for device type %s", len(entities), device_type
    )


class EcoFlowSelect(EcoFlowBaseEntity, SelectEntity):
    """Representation of an EcoFlow select entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        select_key: str,
        select_def: dict[str, Any],
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, select_key)
        self._select_key = select_key
        self._select_def = select_def
        self._attr_unique_id = f"{entry.entry_id}_{select_key}"
        self._attr_name = select_def["name"]
        self._attr_translation_key = select_key
        self._attr_icon = select_def.get("icon")

        # Set options from config
        self._options_map = select_def["options"]
        self._attr_options = list(self._options_map.keys())

        # Create reverse map for value to option
        self._value_to_option = {v: k for k, v in self._options_map.items()}

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        # Handle local settings (like update_interval)
        if self._select_def.get("is_local"):
            if self._select_key == "update_interval":
                value = self.coordinator.update_interval_seconds
                return self._value_to_option.get(value)
            return None

        # Handle device settings
        if not self.coordinator.data:
            return None

        # Special handling for energy strategy mode
        if self._select_key == "energy_strategy_mode":
            # Check which mode is currently active
            if self.coordinator.data.get(
                "energyStrategyOperateMode.operateSelfPoweredOpen", False
            ):
                return "Self-Powered"
            elif self.coordinator.data.get(
                "energyStrategyOperateMode.operateTouModeOpen", False
            ):
                return "TOU"
            else:
                return "Off"

        # Standard handling for other entities
        state_key = self._select_def["state_key"]
        value = self.coordinator.data.get(state_key)

        if value is None:
            return None

        # Convert value to option string
        return self._value_to_option.get(value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self._options_map:
            _LOGGER.error("Invalid option %s for %s", option, self._select_key)
            return

        value = self._options_map[option]

        # Handle local settings (like update_interval)
        if self._select_def.get("is_local"):
            if self._select_key == "update_interval":
                _LOGGER.info("Setting update interval to %s seconds", value)
                await self.coordinator.async_set_update_interval(value)
                # Trigger state update
                self.async_write_ha_state()
            return

        # Handle device settings
        command_key = self._select_def["command_key"]
        device_sn = self.coordinator.device_sn

        # Special handling for energy strategy mode with nested parameters
        if self._select_key == "energy_strategy_mode":
            # Map option to nested parameters
            option_to_params = {
                "off": {
                    "operateSelfPoweredOpen": False,
                    "operateTouModeOpen": False,
                    "operateScheduledOpen": False,
                    "operateIntelligentScheduleModeOpen": False,
                },
                "self_powered": {
                    "operateSelfPoweredOpen": True,
                    "operateTouModeOpen": False,
                    "operateScheduledOpen": False,
                    "operateIntelligentScheduleModeOpen": False,
                },
                "tou": {
                    "operateSelfPoweredOpen": False,
                    "operateTouModeOpen": True,
                    "operateScheduledOpen": False,
                    "operateIntelligentScheduleModeOpen": False,
                },
            }

            params = {command_key: option_to_params[value]}
        else:
            # Standard handling for other entities
            params = {command_key: value}

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
            _LOGGER.error("Failed to set %s to %s: %s", self._select_key, option, err)
            raise


class EcoFlowDeltaProSelect(EcoFlowBaseEntity, SelectEntity):
    """Representation of an EcoFlow Delta Pro select entity.

    Uses the Delta Pro API format with cmdSet and id parameters.
    """

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        select_key: str,
        select_def: dict[str, Any],
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, select_key)
        self._select_key = select_key
        self._select_def = select_def
        self._attr_unique_id = f"{entry.entry_id}_{select_key}"
        self._attr_name = select_def["name"]
        self._attr_translation_key = select_key
        self._attr_icon = select_def.get("icon")

        # Set options from config
        self._options_map = select_def["options"]
        self._attr_options = list(self._options_map.keys())

        # Create reverse map for value to option
        self._value_to_option = {v: k for k, v in self._options_map.items()}

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None

        state_key = self._select_def["state_key"]
        value = self.coordinator.data.get(state_key)

        if value is None:
            return None

        # Convert value to option string
        return self._value_to_option.get(value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option using Delta Pro API format."""
        if option not in self._options_map:
            _LOGGER.error("Invalid option %s for %s", option, self._select_key)
            return

        value = self._options_map[option]
        device_sn = self.coordinator.device_sn
        cmd_set = self._select_def["cmd_set"]
        cmd_id = self._select_def["cmd_id"]
        param_key = self._select_def["param_key"]

        # Build command payload according to Delta Pro API format
        payload = {
            "sn": device_sn,
            "params": {
                "cmdSet": cmd_set,
                "id": cmd_id,
                param_key: value,
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
            _LOGGER.error("Failed to set %s to %s: %s", self._select_key, option, err)
            raise
