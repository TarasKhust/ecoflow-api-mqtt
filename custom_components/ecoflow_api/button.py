"""Button platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .commands import build_command
from .commands.base import CommandFormat
from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowButtonDef
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(  # type: ignore[explicit-any]
    hass: HomeAssistant,
    entry: ConfigEntry,  # type: ignore[explicit-any]
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow button entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    if not profile or not profile.buttons:
        return

    entities = [EcoFlowButton(coordinator, defn, profile.command_format) for defn in profile.buttons]
    async_add_entities(entities)
    _LOGGER.debug("Added %d button entities for %s", len(entities), profile.device_type)


class EcoFlowButton(EcoFlowBaseEntity, ButtonEntity):
    """Representation of an EcoFlow button entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        defn: EcoFlowButtonDef,
        cmd_format: CommandFormat,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._cmd_format = cmd_format
        self._attr_name = defn.name
        self._attr_icon = defn.icon

    async def async_press(self) -> None:
        """Handle the button press."""
        payload = build_command(
            self._cmd_format,
            self.coordinator.device_sn,
            {self._defn.param_key: self._defn.param_value},
            **self._defn.command_params,
        )

        try:
            await self.coordinator.async_send_command(payload)
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to press %s: %s", self._defn.key, err)
            raise
