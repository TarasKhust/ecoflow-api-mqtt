"""Select platform for EcoFlow API integration."""
from __future__ import annotations

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


# AC Standby time options (minutes)
AC_STANDBY_OPTIONS = {
    "Never": 0,
    "30 minutes": 30,
    "1 hour": 60,
    "2 hours": 120,
    "4 hours": 240,
    "6 hours": 360,
    "12 hours": 720,
    "24 hours": 1440,
}

# DC Standby time options (minutes)
DC_STANDBY_OPTIONS = {
    "Never": 0,
    "30 minutes": 30,
    "1 hour": 60,
    "2 hours": 120,
    "4 hours": 240,
    "6 hours": 360,
    "12 hours": 720,
    "24 hours": 1440,
}

# LCD Standby time options (seconds)
LCD_STANDBY_OPTIONS = {
    "Never": 0,
    "10 seconds": 10,
    "30 seconds": 30,
    "1 minute": 60,
    "2 minutes": 120,
    "5 minutes": 300,
}

# Charging mode options (for certain models)
CHARGING_MODE_OPTIONS = {
    "Standard": 0,
    "Silent": 1,
    "Turbo": 2,
}

# AC output frequency options
AC_FREQUENCY_OPTIONS = {
    "50 Hz": 50,
    "60 Hz": 60,
}


# Select definitions for Delta Pro 3
DELTA_PRO_3_SELECT_DEFINITIONS = {
    "ac_standby_time": {
        "name": "AC Standby Time",
        "key": "acStandbyTime",
        "options": AC_STANDBY_OPTIONS,
        "icon": "mdi:timer-outline",
        "method": "async_set_ac_standby_time",
    },
    "dc_standby_time": {
        "name": "DC Standby Time",
        "key": "dcStandbyTime",
        "options": DC_STANDBY_OPTIONS,
        "icon": "mdi:timer-outline",
        "method": "async_set_dc_standby_time",
    },
    "lcd_standby_time": {
        "name": "Screen Standby Time",
        "key": "lcdOffTime",
        "options": LCD_STANDBY_OPTIONS,
        "icon": "mdi:monitor",
        "method": "async_set_lcd_standby_time",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow select entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowSelect] = []
    
    for select_key, select_def in DELTA_PRO_3_SELECT_DEFINITIONS.items():
        entities.append(
            EcoFlowSelect(
                coordinator=coordinator,
                select_key=select_key,
                select_def=select_def,
            )
        )
        _LOGGER.debug("Adding select: %s", select_def["name"])

    async_add_entities(entities)
    _LOGGER.info("Added %d select entities for %s", len(entities), coordinator.device_sn)


class EcoFlowSelect(EcoFlowBaseEntity, SelectEntity):
    """EcoFlow select entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        select_key: str,
        select_def: dict[str, Any],
    ) -> None:
        """Initialize the select entity.
        
        Args:
            coordinator: Data update coordinator
            select_key: Unique key for this select
            select_def: Select definition dictionary
        """
        super().__init__(coordinator, select_key)
        
        self._select_def = select_def
        self._data_key = select_def.get("key", select_key)
        self._method_name = select_def["method"]
        self._options_map = select_def["options"]
        self._reverse_options_map = {v: k for k, v in self._options_map.items()}
        
        # Set entity attributes from definition
        self._attr_name = select_def["name"]
        self._attr_icon = select_def.get("icon")
        self._attr_options = list(self._options_map.keys())

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None
            
        value = self.coordinator.data.get(self._data_key)
        
        if value is None:
            return None
            
        # Convert numeric value to option name
        return self._reverse_options_map.get(int(value))

    async def async_select_option(self, option: str) -> None:
        """Select an option.
        
        Args:
            option: Option to select
        """
        _LOGGER.info(
            "Setting %s to %s for %s",
            self._attr_name,
            option,
            self.coordinator.device_sn
        )
        
        # Convert option name to numeric value
        value = self._options_map.get(option)
        
        if value is None:
            _LOGGER.error("Invalid option: %s", option)
            return
            
        method = getattr(self.coordinator, self._method_name)
        await method(value)




