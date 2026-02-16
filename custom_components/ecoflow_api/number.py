"""Number platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .commands import build_command
from .const import DEFAULT_POWER_STEP, DOMAIN, OPTS_POWER_STEP
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowNumberDef
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    if not profile or not profile.numbers:
        return

    entities = [EcoFlowNumber(coordinator, entry, defn, profile.command_format) for defn in profile.numbers]
    async_add_entities(entities)
    _LOGGER.debug("Added %d number entities for %s", len(entities), profile.device_type)


class EcoFlowNumber(EcoFlowBaseEntity, NumberEntity):
    """Unified EcoFlow number entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        defn: EcoFlowNumberDef,
        cmd_format: Any,
    ) -> None:
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._cmd_format = cmd_format
        self._entry = entry
        self._attr_name = defn.name
        self._attr_native_min_value = defn.min_value
        self._attr_native_max_value = defn.max_value
        self._attr_native_unit_of_measurement = defn.unit
        self._attr_icon = defn.icon
        self._attr_mode = defn.mode

        # Use configurable power step for AC Charging Power
        if defn.key == "ac_charge_power":
            self._attr_native_step = entry.options.get(OPTS_POWER_STEP, DEFAULT_POWER_STEP)
        else:
            self._attr_native_step = defn.step

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._defn.state_key)
        if value is None:
            return None

        # Apply value_to_ui mapping if defined (e.g., Smart Plug brightness 0-1023 -> 0-100%)
        if self._defn.value_to_ui:
            value = self._defn.value_to_ui(value)

        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        # Clamp to limits
        value = max(self._defn.min_value, min(self._defn.max_value, value))

        # Apply value_from_ui mapping if defined (e.g., Smart Plug brightness 0-100% -> 0-1023)
        api_value = value
        if self._defn.value_from_ui:
            api_value = self._defn.value_from_ui(value)

        int_value = int(api_value)

        # Handle nested parameters (e.g., backup reserve level)
        if self._defn.nested_params:
            # Replace None values with the actual value
            nested = {}
            for k, v in self._defn.nested_params.items():
                nested[k] = int_value if v is None else v
            params = {self._defn.param_key: nested}
        else:
            params = {self._defn.param_key: int_value}

        payload = build_command(
            self._cmd_format,
            self.coordinator.device_sn,
            params,
            **self._defn.command_params,
        )

        try:
            await self.coordinator.async_send_command(payload)
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set %s to %s: %s", self._defn.key, int_value, err)
            raise
