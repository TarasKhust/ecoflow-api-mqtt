"""Button platform for EcoFlow API integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity
from .hybrid_coordinator import EcoFlowHybridCoordinator

_LOGGER = logging.getLogger(__name__)


class EcoFlowWakeDeviceButton(EcoFlowBaseEntity, ButtonEntity):
    """Button to manually wake up EcoFlow device."""
    
    _attr_icon = "mdi:power-wake"
    _attr_name = "Wake Device"
    
    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        device_sn: str,
        device_type: str,
    ) -> None:
        """Initialize wake device button."""
        super().__init__(coordinator, device_sn, device_type)
        self._attr_unique_id = f"{device_sn}_wake_device"
        self._attr_translation_key = "wake_device"
    
    async def async_press(self) -> None:
        """Handle button press - wake up device."""
        _LOGGER.info("🔔 Manual wake-up requested for device %s", self.device_sn)
        
        # Check if coordinator supports wake-up
        if isinstance(self.coordinator, EcoFlowHybridCoordinator):
            # Use aggressive wake-up for manual trigger
            await self.coordinator.async_wake_device()
            _LOGGER.info("✅ Device %s woken up successfully", self.device_sn)
        else:
            # For REST-only coordinator, just refresh data
            _LOGGER.info("Refreshing data for device %s (REST-only mode)", self.device_sn)
            await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow button entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_sn = entry.data["device_sn"]
    device_type = entry.data.get("device_type", "unknown")
    
    # Add wake device button
    async_add_entities([
        EcoFlowWakeDeviceButton(coordinator, device_sn, device_type)
    ])

