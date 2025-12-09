"""Diagnostics support for EcoFlow API integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_DEVICE_SN
from .coordinator import EcoFlowDataCoordinator

# Keys to redact from diagnostics
TO_REDACT = {
    CONF_ACCESS_KEY,
    CONF_SECRET_KEY,
    CONF_DEVICE_SN,
    "sn",
    "serial_number",
    "serialNumber",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        Diagnostics data dictionary
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Redact sensitive data from config entry
    redacted_config = async_redact_data(entry.data, TO_REDACT)
    
    # Get device data (redacted)
    device_data = {}
    if coordinator.data:
        device_data = async_redact_data(coordinator.data, TO_REDACT)
    
    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": redacted_config,
            "options": dict(entry.options),
        },
        "coordinator": {
            "device_type": coordinator.device_type,
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "device_info": {
            "identifiers": list(coordinator.device_info.get("identifiers", [])),
            "name": coordinator.device_info.get("name"),
            "manufacturer": coordinator.device_info.get("manufacturer"),
            "model": coordinator.device_info.get("model"),
        },
        "device_data": device_data,
    }


