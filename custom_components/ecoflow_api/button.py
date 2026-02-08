"""Button platform for EcoFlow API integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_DELTA_PRO_3,
    DEVICE_TYPE_STREAM_ULTRA_X,
    DOMAIN,
)
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity
from .hybrid_coordinator import EcoFlowHybridCoordinator

_LOGGER = logging.getLogger(__name__)


# Button definitions for Delta Pro 3 based on API documentation
DELTA_PRO_3_BUTTON_DEFINITIONS = {
    "power_off": {
        "name": "Power Off",
        "command_key": "cfgPowerOff",
        "icon": "mdi:power",
        "device_class": None,
    },
}

# Button definitions for Stream Ultra X
STREAM_ULTRA_X_BUTTON_DEFINITIONS = {
    "power_off": {
        "name": "Power Off",
        "command_key": "cfgPowerOff",
        "icon": "mdi:power",
        "device_class": None,
    },
}

# Map device types to button definitions
DEVICE_BUTTON_MAP = {
    DEVICE_TYPE_DELTA_PRO_3: DELTA_PRO_3_BUTTON_DEFINITIONS,
    DEVICE_TYPE_STREAM_ULTRA_X: STREAM_ULTRA_X_BUTTON_DEFINITIONS,
    "delta_pro_3": DELTA_PRO_3_BUTTON_DEFINITIONS,
    "stream_ultra_x": STREAM_ULTRA_X_BUTTON_DEFINITIONS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow button entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_type = coordinator.device_type

    # Get button definitions for this device type
    button_definitions = DEVICE_BUTTON_MAP.get(device_type)

    if not button_definitions:
        _LOGGER.debug("No button definitions for device type %s", device_type)
        return

    entities: list[ButtonEntity] = []

    for button_key, button_def in button_definitions.items():
        entities.append(
            EcoFlowButton(
                coordinator=coordinator,
                entry=entry,
                button_key=button_key,
                button_def=button_def,
            )
        )

    async_add_entities(entities)
    _LOGGER.info(
        "Added %d button entities for device type %s", len(entities), device_type
    )


class EcoFlowButton(EcoFlowBaseEntity, ButtonEntity):
    """Representation of an EcoFlow button entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        button_key: str,
        button_def: dict[str, Any],
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, button_key)
        self._button_key = button_key
        self._button_def = button_def
        self._attr_unique_id = f"{entry.entry_id}_{button_key}"
        self._attr_name = button_def["name"]
        self._attr_has_entity_name = True
        self._attr_translation_key = button_key
        self._attr_icon = button_def.get("icon")
        self._attr_device_class = button_def.get("device_class")

    async def async_press(self) -> None:
        """Handle the button press via MQTT (preferred) or REST API."""
        command_key = self._button_def["command_key"]
        device_sn = self.coordinator.device_sn

        # Build command payload according to Delta Pro 3 API format
        payload = {
            "sn": device_sn,
            "cmdId": 17,
            "dirDest": 1,
            "dirSrc": 1,
            "cmdFunc": 254,
            "dest": 2,
            "needAck": True,
            "params": {command_key: True},
        }

        try:
            # Use hybrid coordinator's send_command method (MQTT preferred, REST fallback)
            if isinstance(self.coordinator, EcoFlowHybridCoordinator):
                success = await self.coordinator.async_send_command(payload)
                if not success:
                    raise Exception("Command failed via both MQTT and REST API")
            else:
                # Fallback to REST API for non-hybrid coordinators
                await self.coordinator.api_client.set_device_quota(
                    device_sn=device_sn,
                    cmd_code=payload,
                )
            _LOGGER.info("Power off command sent to device %s", device_sn)
        except Exception as err:
            _LOGGER.error("Failed to send power off command: %s", err)
            raise
