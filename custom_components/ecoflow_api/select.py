"""Select platform for EcoFlow API integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow select entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowSelect] = []
    
    for select_key, select_def in DELTA_PRO_3_SELECT_DEFINITIONS.items():
        entities.append(
            EcoFlowSelect(
                coordinator=coordinator,
                entry=entry,
                select_key=select_key,
                select_def=select_def,
            )
        )
    
    async_add_entities(entities)
    _LOGGER.info("Added %d select entities", len(entities))


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
        super().__init__(coordinator, entry)
        self._select_key = select_key
        self._select_def = select_def
        self._attr_unique_id = f"{entry.entry_id}_{select_key}"
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
        device_sn = self.coordinator.config_entry.data["device_sn"]
        
        # Build command payload according to Delta Pro 3 API format
        payload = {
            "sn": device_sn,
            "cmdId": 17,
            "dirDest": 1,
            "dirSrc": 1,
            "cmdFunc": 254,
            "dest": 2,
            "needAck": True,
            "params": {
                command_key: value
            }
        }
        
        _LOGGER.debug(
            "Sending select command for %s: %s = %s (%s)",
            self._select_key,
            command_key,
            value,
            option
        )
        
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
                self._select_key,
                option,
                err
            )
            raise
