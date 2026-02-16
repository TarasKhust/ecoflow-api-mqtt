"""Select platform for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .commands import build_command
from .commands.base import CommandFormat
from .const import DOMAIN, JsonVal
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowSelectDef
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Local-only select definitions (not device-specific)
_UPDATE_INTERVAL_SELECT = EcoFlowSelectDef(
    key="update_interval",
    name="Update Interval",
    param_key="",
    options={
        "5 seconds (Fast)": 5,
        "10 seconds": 10,
        "15 seconds (Recommended)": 15,
        "30 seconds": 30,
        "60 seconds (Slow)": 60,
    },
    icon="mdi:update",
    is_local=True,
)


async def async_setup_entry(  # type: ignore[explicit-any]
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow select entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    entities: list[SelectEntity] = []

    # Always add the update interval select (local-only)
    entities.append(EcoFlowSelect(coordinator, _UPDATE_INTERVAL_SELECT, None))

    # Add device-specific selects
    if profile and profile.selects:
        entities.extend(EcoFlowSelect(coordinator, defn, profile.command_format) for defn in profile.selects)

    async_add_entities(entities)
    _LOGGER.debug("Added %d select entities for %s", len(entities), coordinator.device_type)


class EcoFlowSelect(EcoFlowBaseEntity, SelectEntity):
    """Unified EcoFlow select entity."""

    def __init__(
        self, coordinator: EcoFlowDataCoordinator, defn: EcoFlowSelectDef, cmd_format: CommandFormat | None
    ) -> None:
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._cmd_format = cmd_format
        self._attr_name = defn.name
        self._attr_icon = defn.icon
        self._options_map = defn.options
        self._attr_options = list(defn.options.keys())
        # Reverse mapping only for scalar options (nested dict options can't be dict keys)
        self._value_to_option: dict[int | str, str] = {
            v: k for k, v in defn.options.items() if isinstance(v, (int, str))
        }

    @property
    def current_option(self) -> str | None:
        # Handle local-only settings
        if self._defn.is_local:
            if self._defn.key == "update_interval":
                value = self.coordinator.update_interval_seconds
                return self._value_to_option.get(value)
            return None

        if not self.coordinator.data:
            return None

        # Handle nested params special cases (energy strategy mode, operating mode)
        if self._defn.nested_params and self._defn.key in ("energy_strategy_mode", "operating_mode"):
            return self._get_nested_state()

        state_key = self._defn.state_key
        if not state_key:
            return None

        raw = self.coordinator.data.get(state_key)
        if raw is None:
            return None

        scalar = raw if isinstance(raw, (int, str)) else None
        if scalar is None:
            return None
        return self._value_to_option.get(scalar)

    def _get_nested_state(self) -> str | None:
        """Get state for nested param selects by checking boolean flags."""
        data = self.coordinator.data
        if not data:
            return None

        # Check each option's nested value to find the active one
        for option_name, option_value in self._options_map.items():
            if isinstance(option_value, dict):
                # Nested params: check if the flag is set
                for flag_key, flag_val in option_value.items():
                    full_key = f"{self._defn.state_key}.{flag_key}" if self._defn.state_key else flag_key
                    if data.get(full_key) == flag_val:
                        return option_name

        # For energy_strategy_mode with string values (off, self_powered, tou)
        if self._defn.key == "energy_strategy_mode":
            if data.get("energyStrategyOperateMode.operateSelfPoweredOpen", False):
                return "Self-Powered"
            if data.get("energyStrategyOperateMode.operateTouModeOpen", False):
                return "TOU"
            return "Off"

        return None

    async def async_select_option(self, option: str) -> None:
        if option not in self._options_map:
            _LOGGER.error("Invalid option %s for %s", option, self._defn.key)
            return

        value = self._options_map[option]

        # Handle local-only settings
        if self._defn.is_local:
            if self._defn.key == "update_interval" and isinstance(value, int):
                await self.coordinator.async_set_update_interval(value)
                self.async_write_ha_state()
            return

        # Build params
        params: dict[str, JsonVal] = {self._defn.param_key: value}  # type: ignore[dict-item]

        # Special case: energy_strategy_mode with string values
        if self._defn.key == "energy_strategy_mode" and isinstance(value, str):
            option_to_params: dict[str, dict[str, JsonVal]] = {
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
            params = {self._defn.param_key: option_to_params.get(value, {})}

        if self._cmd_format is None:
            _LOGGER.error("Command format required for non-local select %s", self._defn.key)
            return
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
            _LOGGER.error("Failed to set %s to %s: %s", self._defn.key, option, err)
            raise
