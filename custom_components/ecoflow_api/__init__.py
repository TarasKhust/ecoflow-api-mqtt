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
from .const import (
    CONF_ACCESS_KEY,
    CONF_DEVICE_SN,
    CONF_DEVICE_TYPE,
    CONF_MQTT_ENABLED,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_REGION,
    CONF_SECRET_KEY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    REGION_EU,
)
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
    Platform.BUTTON,
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

    # Check which credentials are available (must exist AND not be empty)
    # Check both entry.data and entry.options (MQTT creds may be in options for existing entries)
    has_api_keys = bool(entry.data.get(CONF_ACCESS_KEY)) and bool(entry.data.get(CONF_SECRET_KEY))
    has_mqtt_creds = (
        (bool(entry.data.get(CONF_MQTT_USERNAME)) and bool(entry.data.get(CONF_MQTT_PASSWORD)))
        or (bool(entry.options.get(CONF_MQTT_USERNAME)) and bool(entry.options.get(CONF_MQTT_PASSWORD)))
    )

    # Require at least one set of credentials
    if not has_api_keys and not has_mqtt_creds:
        _LOGGER.error(
            "No credentials provided. Please add either API keys or MQTT credentials."
        )
        return False

    # Create API client if API keys provided
    client = None
    if has_api_keys:
        session = async_get_clientsession(hass)
        region = entry.data.get(CONF_REGION, REGION_EU)
        client = EcoFlowApiClient(
            access_key=entry.data[CONF_ACCESS_KEY],
            secret_key=entry.data[CONF_SECRET_KEY],
            session=session,
            region=region,
        )
        _LOGGER.info("✅ API client created with Developer API keys")
    else:
        _LOGGER.info("⚠️ MQTT-only mode: No API keys provided, device control will be limited")

    # Get update interval from options (or data for backward compatibility)
    update_interval = (
        entry.options.get(CONF_UPDATE_INTERVAL)
        or entry.data.get(CONF_UPDATE_INTERVAL)
        or DEFAULT_UPDATE_INTERVAL
    )

    # Get MQTT settings from options OR data (priority: options > data)
    mqtt_enabled = entry.options.get(CONF_MQTT_ENABLED, has_mqtt_creds)  # Auto-enable if credentials in data
    mqtt_username = entry.options.get(CONF_MQTT_USERNAME) or entry.data.get(CONF_MQTT_USERNAME)
    mqtt_password = entry.options.get(CONF_MQTT_PASSWORD) or entry.data.get(CONF_MQTT_PASSWORD)
    certificate_account = None

    # If MQTT enabled and API client available, try to get certificateAccount from API
    # Otherwise use user-provided MQTT credentials directly
    if mqtt_enabled and client:
        try:
            _LOGGER.info("MQTT enabled, fetching certificate credentials from API...")
            mqtt_creds = await client.get_mqtt_credentials()
            certificate_account = mqtt_creds.get("certificateAccount")
            certificate_password = mqtt_creds.get("certificatePassword")

            if certificate_account and certificate_password:
                _LOGGER.info(
                    "✅ Successfully obtained MQTT certificate credentials from API"
                )
                mqtt_username = certificate_account
                mqtt_password = certificate_password
            else:
                _LOGGER.warning(
                    "⚠️ Failed to get MQTT certificate credentials from API, "
                    "using user-provided credentials"
                )
        except Exception as err:
            _LOGGER.error(
                "❌ Error fetching MQTT certificate credentials: %s. "
                "Using user-provided credentials.",
                err,
            )
    elif mqtt_enabled and not client:
        _LOGGER.info(
            "📱 MQTT-only mode: Using user-provided credentials "
            "(email/password from EcoFlow app)"
        )

    # Create coordinator based on available credentials
    coordinator: EcoFlowDataCoordinator | EcoFlowHybridCoordinator
    if mqtt_enabled and mqtt_username and mqtt_password:
        # MQTT mode (with or without REST API)
        mode = "hybrid (REST + MQTT)" if client else "MQTT-only"
        _LOGGER.info(
            "Creating %s coordinator for device %s",
            mode,
            entry.data[CONF_DEVICE_SN],
        )
        coordinator = EcoFlowHybridCoordinator(
            hass=hass,
            client=client,  # May be None for MQTT-only mode
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
    elif client:
        # REST-only mode (no MQTT)
        _LOGGER.info(
            "Creating REST-only coordinator for device %s", entry.data[CONF_DEVICE_SN]
        )
        coordinator = EcoFlowDataCoordinator(
            hass=hass,
            client=client,
            device_sn=entry.data[CONF_DEVICE_SN],
            device_type=entry.data.get(CONF_DEVICE_TYPE, "unknown"),
            update_interval=update_interval,
            config_entry=entry,
        )
    else:
        # Should never reach here due to earlier validation
        _LOGGER.error("No valid configuration for coordinator")
        return False

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Log connection status
    device_sn = entry.data[CONF_DEVICE_SN]

    if isinstance(coordinator, EcoFlowHybridCoordinator):
        if client and coordinator.mqtt_connected:
            # Hybrid mode: both REST and MQTT
            _LOGGER.info("✅ Hybrid mode active for device %s (REST + MQTT)", device_sn)
        elif not client and coordinator.mqtt_connected:
            # MQTT-only mode
            _LOGGER.info("✅ MQTT-only mode active for device %s (read-only, commands via MQTT)", device_sn)
        elif client and not coordinator.mqtt_connected:
            # REST-only fallback (MQTT failed)
            _LOGGER.warning(
                "⚠️ MQTT connection failed for device %s, using REST-only mode", device_sn
            )
        else:
            # No connection at all
            _LOGGER.error("❌ No connection established for device %s", device_sn)
    else:
        # REST-only coordinator
        _LOGGER.info("✅ REST-only mode active for device %s", device_sn)

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("🔋 EcoFlow API integration ready for device %s", device_sn)

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
            "EcoFlow API integration unloaded for device %s", entry.data[CONF_DEVICE_SN]
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
