"""Config entry migration helpers for EcoFlow API integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import (
    DEFAULT_POWER_STEP,
    DEFAULT_REFRESH_PERIOD_SEC,
    OPTS_DIAGNOSTIC_MODE,
    OPTS_POWER_STEP,
    OPTS_REFRESH_PERIOD_SEC,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Current config version
CONFIG_VERSION = 2


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry to latest version.

    Args:
        hass: Home Assistant instance
        config_entry: Config entry to migrate

    Returns:
        True if migration was successful
    """
    version = config_entry.version
    updated = False

    if version == 1:
        _LOGGER.info(
            "Migrating config entry %s from version %d to %d",
            config_entry.entry_id,
            version,
            CONFIG_VERSION,
        )

        # Migrate from version 1 to 2: Add device options
        new_data = dict(config_entry.data)
        new_options = dict(config_entry.options)

        # Add default device options if not present
        if OPTS_REFRESH_PERIOD_SEC not in new_options:
            new_options[OPTS_REFRESH_PERIOD_SEC] = DEFAULT_REFRESH_PERIOD_SEC
        if OPTS_POWER_STEP not in new_options:
            new_options[OPTS_POWER_STEP] = DEFAULT_POWER_STEP
        if OPTS_DIAGNOSTIC_MODE not in new_options:
            new_options[OPTS_DIAGNOSTIC_MODE] = False

        # Update entry
        hass.config_entries.async_update_entry(
            config_entry,
            version=CONFIG_VERSION,
            data=new_data,
            options=new_options,
        )
        updated = True
        _LOGGER.info(
            "Successfully migrated config entry %s to version %d",
            config_entry.entry_id,
            CONFIG_VERSION,
        )

    return updated
