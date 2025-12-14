"""EcoFlow API Integration for Home Assistant.

This integration provides direct access to EcoFlow devices using the official
Developer API. It supports various EcoFlow power stations including Delta Pro 3.

Documentation:
- EcoFlow API: https://developer-eu.ecoflow.com/us/document/introduction
- Delta Pro 3: https://developer-eu.ecoflow.com/us/document/deltaPro3
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcoFlowApiClient
from .const import (CONF_ACCESS_KEY, CONF_DEVICE_SN, CONF_DEVICE_TYPE,
                    CONF_MQTT_ENABLED, CONF_MQTT_PASSWORD, CONF_MQTT_USERNAME,
                    CONF_SECRET_KEY, CONF_UPDATE_INTERVAL,
                    DEFAULT_UPDATE_INTERVAL, DOMAIN)
from .coordinator import EcoFlowDataCoordinator
from .hybrid_coordinator import EcoFlowHybridCoordinator
from .migrations import async_migrate_entry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoFlow API from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        True if setup was successful
    """
    # Migrate config entry if needed
    await async_migrate_entry(hass, entry)
    
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    session = async_get_clientsession(hass)
    client = EcoFlowApiClient(
        access_key=entry.data[CONF_ACCESS_KEY],
        secret_key=entry.data[CONF_SECRET_KEY],
        session=session,
    )

    # Get update interval from options (or data for backward compatibility)
    update_interval = (
        entry.options.get(CONF_UPDATE_INTERVAL) or 
        entry.data.get(CONF_UPDATE_INTERVAL) or 
        DEFAULT_UPDATE_INTERVAL
    )
    
    # Get MQTT settings from options
    mqtt_enabled = entry.options.get(CONF_MQTT_ENABLED, False)
    mqtt_username = entry.options.get(CONF_MQTT_USERNAME)
    mqtt_password = entry.options.get(CONF_MQTT_PASSWORD)
    certificate_account = None
    
    # If MQTT enabled, get certificateAccount and certificatePassword from API
    if mqtt_enabled:
        try:
            _LOGGER.info("MQTT enabled, fetching MQTT credentials from API...")
            mqtt_creds = await client.get_mqtt_credentials()
            certificate_account = mqtt_creds.get("certificateAccount")
            certificate_password = mqtt_creds.get("certificatePassword")
            
            if certificate_account and certificate_password:
                _LOGGER.info("Successfully obtained MQTT credentials from API")
                mqtt_username = certificate_account
                mqtt_password = certificate_password
            else:
                _LOGGER.warning("Failed to get MQTT credentials from API, using manual credentials if provided")
        except Exception as err:
            _LOGGER.error("Error fetching MQTT credentials: %s. Using manual credentials if provided.", err)
    
    # Create coordinator (hybrid if MQTT enabled, otherwise standard)
    coordinator: EcoFlowDataCoordinator | EcoFlowHybridCoordinator
    if mqtt_enabled and mqtt_username and mqtt_password:
        _LOGGER.info("Creating hybrid coordinator (REST + MQTT) for device %s", entry.data[CONF_DEVICE_SN])
        coordinator = EcoFlowHybridCoordinator(
            hass=hass,
            client=client,
            device_sn=entry.data[CONF_DEVICE_SN],
            device_type=entry.data.get(CONF_DEVICE_TYPE, "unknown"),
            update_interval=update_interval,
            config_entry=entry,
            mqtt_username=mqtt_username,
            mqtt_password=mqtt_password,
            mqtt_enabled=True,
            certificate_account=certificate_account,  # Pass certificate account for topics
        )
        # Set up MQTT
        await coordinator.async_setup()
    else:
        _LOGGER.info("Creating REST-only coordinator for device %s", entry.data[CONF_DEVICE_SN])
        coordinator = EcoFlowDataCoordinator(
            hass=hass,
            client=client,
            device_sn=entry.data[CONF_DEVICE_SN],
            device_type=entry.data.get(CONF_DEVICE_TYPE, "unknown"),
            update_interval=update_interval,
            config_entry=entry,
        )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Log connection status
    device_sn = entry.data[CONF_DEVICE_SN]
    _LOGGER.info("✅ REST API connected for device %s", device_sn)
    
    if isinstance(coordinator, EcoFlowHybridCoordinator):
        if coordinator.mqtt_connected:
            _LOGGER.info("✅ MQTT connected for device %s (hybrid mode)", device_sn)
        else:
            _LOGGER.warning("⚠️ MQTT not connected for device %s (REST-only mode)", device_sn)

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "🔋 EcoFlow API integration ready for device %s",
        device_sn
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        True if unload was successful
    """
    # Shutdown MQTT if hybrid coordinator
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator and isinstance(coordinator, EcoFlowHybridCoordinator):
        await coordinator.async_shutdown()
        _LOGGER.info("Shut down MQTT for device %s", entry.data[CONF_DEVICE_SN])
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info(
            "EcoFlow API integration unloaded for device %s",
            entry.data[CONF_DEVICE_SN]
        )

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry.
    
    Cleans up device and entity registry entries.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry being removed
    """
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    # Clean up device registry
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for device in devices:
        device_registry.async_remove_device(device.id)
    
    # Clean up entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    for entity in entities:
        entity_registry.async_remove(entity.entity_id)
    
    _LOGGER.info(
        "Cleaned up %d devices and %d entities for config entry %s",
        len(devices),
        len(entities),
        entry.entry_id,
    )


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)



