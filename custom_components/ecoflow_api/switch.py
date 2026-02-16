"""Switch platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .commands import build_command
from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowSwitchDef
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switch entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    if not profile or not profile.switches:
        return

    entities = [EcoFlowSwitch(coordinator, defn, profile.command_format) for defn in profile.switches]
    async_add_entities(entities)
    _LOGGER.debug("Added %d switch entities for %s", len(entities), profile.device_type)


class EcoFlowSwitch(EcoFlowBaseEntity, SwitchEntity):
    """Unified EcoFlow switch entity."""

    def __init__(self, coordinator, defn: EcoFlowSwitchDef, cmd_format) -> None:
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._cmd_format = cmd_format
        self._attr_name = defn.name
        self._attr_device_class = defn.device_class

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None

        state_key = self._defn.state_key
        value = self.coordinator.data.get(state_key)

        if value is None:
            return None

        # Interpret state value based on state_interpreter
        interpreter = self._defn.state_interpreter

        if interpreter == "flow_info":
            # flow_info: 0=off, 2=on (Delta Pro 3 flowInfo* keys)
            result = value == 2
        elif interpreter == "int01":
            # int01: 0=off, 1=on
            if isinstance(value, (int, float)):
                result = int(value) == 1
            elif isinstance(value, str):
                result = value.lower() in ("1", "true", "on")
            else:
                result = bool(value)
        else:
            # "bool" (default) — handle special value_on/value_off
            if self._defn.value_on not in (True, 1) or self._defn.value_off not in (False, 0):
                # Custom values like feed_in_control (1=off, 2=on)
                result = value == self._defn.value_on
            elif isinstance(value, bool):
                result = value
            elif isinstance(value, (int, float)):
                result = int(value) == 1
            elif isinstance(value, str):
                result = value.lower() in ("1", "true", "on")
            else:
                result = bool(value)

        # Handle inverted switches
        if self._defn.inverted:
            return not result
        return result

    @property
    def icon(self) -> str | None:
        if self.is_on:
            return self._defn.icon_on
        return self._defn.icon_off

    async def async_turn_on(self, **kwargs: Any) -> None:
        value = self._defn.value_on
        if self._defn.inverted:
            value = self._defn.value_off
        await self._send_command(value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        value = self._defn.value_off
        if self._defn.inverted:
            value = self._defn.value_on
        await self._send_command(value)

    async def _send_command(self, value: Any) -> None:
        payload = build_command(
            self._cmd_format,
            self.coordinator.device_sn,
            {self._defn.param_key: value},
            **self._defn.command_params,
        )
        try:
            await self.coordinator.async_send_command(payload)
            await asyncio.sleep(3)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set %s: %s", self._defn.key, err)
            raise
