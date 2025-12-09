"""Switch platform for EcoFlow API integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Switch definitions for Delta Pro 3
DELTA_PRO_3_SWITCH_DEFINITIONS = {
    "acOutState": {
        "name": "AC Output",
        "key": "acOutState",
        "icon_on": "mdi:power-plug",
        "icon_off": "mdi:power-plug-off",
        "device_class": SwitchDeviceClass.OUTLET,
        "method": "async_set_ac_output",
    },
    "dcOutState": {
        "name": "DC Output",
        "key": "dcOutState",
        "icon_on": "mdi:current-dc",
        "icon_off": "mdi:current-dc",
        "device_class": SwitchDeviceClass.OUTLET,
        "method": "async_set_dc_output",
    },
    "dc12vOutState": {
        "name": "12V DC Output",
        "key": "dc12vOutState",
        "icon_on": "mdi:car-battery",
        "icon_off": "mdi:car-battery",
        "device_class": SwitchDeviceClass.OUTLET,
        "method": "async_set_12v_dc_output",
    },
    "beepState": {
        "name": "Beeper",
        "key": "beepState",
        "icon_on": "mdi:volume-high",
        "icon_off": "mdi:volume-off",
        "device_class": SwitchDeviceClass.SWITCH,
        "method": "async_set_beep",
    },
    "xBoostState": {
        "name": "X-Boost",
        "key": "xBoostState",
        "icon_on": "mdi:lightning-bolt",
        "icon_off": "mdi:lightning-bolt-outline",
        "device_class": SwitchDeviceClass.SWITCH,
        "method": "async_set_x_boost",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switch entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowSwitch] = []
    
    for switch_key, switch_def in DELTA_PRO_3_SWITCH_DEFINITIONS.items():
        entities.append(
            EcoFlowSwitch(
                coordinator=coordinator,
                switch_key=switch_key,
                switch_def=switch_def,
            )
        )
        _LOGGER.debug("Adding switch: %s", switch_def["name"])

    async_add_entities(entities)
    _LOGGER.info("Added %d switches for %s", len(entities), coordinator.device_sn)


class EcoFlowSwitch(EcoFlowBaseEntity, SwitchEntity):
    """EcoFlow switch entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        switch_key: str,
        switch_def: dict[str, Any],
    ) -> None:
        """Initialize the switch.
        
        Args:
            coordinator: Data update coordinator
            switch_key: Unique key for this switch
            switch_def: Switch definition dictionary
        """
        super().__init__(coordinator, switch_key)
        
        self._switch_def = switch_def
        self._data_key = switch_def.get("key", switch_key)
        self._method_name = switch_def["method"]
        
        # Set entity attributes from definition
        self._attr_name = switch_def["name"]
        self._attr_device_class = switch_def.get("device_class")
        self._icon_on = switch_def.get("icon_on", "mdi:toggle-switch")
        self._icon_off = switch_def.get("icon_off", "mdi:toggle-switch-off")

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        if not self.coordinator.data:
            return None
            
        value = self.coordinator.data.get(self._data_key)
        
        if value is None:
            return None
            
        # Handle different value types
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.lower() in ("1", "true", "on")
            
        return None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return self._icon_on
        return self._icon_off

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        method = getattr(self.coordinator, self._method_name)
        await method(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        method = getattr(self.coordinator, self._method_name)
        await method(False)


