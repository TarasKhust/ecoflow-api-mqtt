"""Diagnostics support for EcoFlow API integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ACCESS_KEY,
    CONF_SECRET_KEY,
    CONF_DEVICE_SN,
    OPTS_DIAGNOSTIC_MODE,
)
from .coordinator import EcoFlowDataCoordinator
from .hybrid_coordinator import EcoFlowHybridCoordinator

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
    
    # Check if diagnostic mode is enabled
    diagnostic_mode = entry.options.get(OPTS_DIAGNOSTIC_MODE, False)
    
    # Redact sensitive data from config entry
    redacted_config = async_redact_data(entry.data, TO_REDACT)
    
    # Get device data (redacted)
    device_data = {}
    if coordinator.data:
        device_data = async_redact_data(coordinator.data, TO_REDACT)
    
    # Build coordinator info
    coordinator_info = {
        "device_type": coordinator.device_type,
        "last_update_success": coordinator.last_update_success,
        "update_interval": str(coordinator.update_interval),
    }
    
    # Add MQTT info if hybrid coordinator
    if isinstance(coordinator, EcoFlowHybridCoordinator):
        coordinator_info["mqtt_connected"] = coordinator.mqtt_connected
        coordinator_info["connection_mode"] = coordinator.connection_mode
    
    # Build diagnostic data if enabled
    diagnostic_data = None
    if diagnostic_mode:
        diagnostic_data = {}
        
        # REST requests
        if hasattr(coordinator, "rest_requests"):
            diagnostic_data["rest_requests"] = list(coordinator.rest_requests)
        
        # MQTT messages (if hybrid)
        if isinstance(coordinator, EcoFlowHybridCoordinator) and hasattr(coordinator, "mqtt_messages"):
            diagnostic_data["mqtt_messages"] = list(coordinator.mqtt_messages)
        
        # Set commands and replies
        if hasattr(coordinator, "set_commands"):
            diagnostic_data["set_commands"] = list(coordinator.set_commands)
        if hasattr(coordinator, "set_replies"):
            diagnostic_data["set_replies"] = list(coordinator.set_replies)
    
    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": redacted_config,
            "options": dict(entry.options),
        },
        "coordinator": coordinator_info,
        "device_info": {
            "identifiers": list(coordinator.device_info.get("identifiers", [])),
            "name": coordinator.device_info.get("name"),
            "manufacturer": coordinator.device_info.get("manufacturer"),
            "model": coordinator.device_info.get("model"),
        },
        "device_data": device_data,
        "diagnostic_data": diagnostic_data,
    }





