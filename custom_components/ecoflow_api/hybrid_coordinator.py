"""Hybrid DataUpdateCoordinator for EcoFlow API (REST + MQTT).

This coordinator combines:
- REST API for device control and fallback polling
- MQTT for real-time sensor updates and additional data
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import EcoFlowApiClient, EcoFlowApiError
from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .mqtt_client import EcoFlowMQTTClient

_LOGGER = logging.getLogger(__name__)


class EcoFlowHybridCoordinator(EcoFlowDataCoordinator):
    """Hybrid coordinator using both REST API and MQTT.
    
    Features:
    - Real-time updates via MQTT
    - Device control via REST API
    - Automatic fallback to REST polling if MQTT unavailable
    - Merges data from both sources
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: EcoFlowApiClient,
        device_sn: str,
        device_type: str,
        update_interval: int = 15,
        config_entry: ConfigEntry | None = None,
        mqtt_username: str | None = None,
        mqtt_password: str | None = None,
        mqtt_enabled: bool = True,
        certificate_account: str | None = None,
    ) -> None:
        """Initialize hybrid coordinator.
        
        Args:
            hass: Home Assistant instance
            client: EcoFlow API client
            device_sn: Device serial number
            device_type: Device type identifier
            update_interval: Update interval in seconds (for REST fallback)
            config_entry: Config entry reference
            mqtt_username: MQTT username (certificateAccount from API)
            mqtt_password: MQTT password (certificatePassword from API)
            mqtt_enabled: Whether to enable MQTT
            certificate_account: Certificate account for MQTT topics (same as username)
        """
        super().__init__(
            hass=hass,
            client=client,
            device_sn=device_sn,
            device_type=device_type,
            update_interval=update_interval,
            config_entry=config_entry,
        )
        
        self.mqtt_enabled = mqtt_enabled
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.certificate_account = certificate_account or mqtt_username
        
        self._mqtt_client: EcoFlowMQTTClient | None = None
        self._mqtt_data: dict[str, Any] = {}
        self._mqtt_connected = False
        self._use_mqtt = False
        
    @property
    def mqtt_connected(self) -> bool:
        """Return MQTT connection status."""
        return self._mqtt_connected
    
    @property
    def connection_mode(self) -> str:
        """Return current connection mode."""
        if self._use_mqtt and self._mqtt_connected:
            return "hybrid"
        elif self._mqtt_connected:
            return "mqtt_standby"
        else:
            return "rest_only"

    async def async_setup(self) -> bool:
        """Set up the coordinator (including MQTT if enabled).
        
        Returns:
            True if setup successful
        """
        # Always try to connect MQTT if enabled
        if self.mqtt_enabled and self.mqtt_username and self.mqtt_password:
            await self._async_setup_mqtt()
        else:
            _LOGGER.info(
                "MQTT disabled or credentials not provided for %s, using REST API only",
                self.device_sn
            )
        
        return True

    async def _async_setup_mqtt(self) -> None:
        """Set up MQTT client."""
        try:
            _LOGGER.info("Setting up MQTT for device %s", self.device_sn)
            
            self._mqtt_client = EcoFlowMQTTClient(
                username=self.mqtt_username,
                password=self.mqtt_password,
                device_sn=self.device_sn,
                on_message_callback=self._handle_mqtt_message,
                certificate_account=self.certificate_account,
            )
            
            # Try to connect
            connected = await self._mqtt_client.async_connect()
            
            if connected:
                self._mqtt_connected = True
                self._use_mqtt = True
                _LOGGER.info("MQTT connected successfully for device %s", self.device_sn)
                
                # Increase REST polling interval since we have real-time updates
                self.update_interval = timedelta(seconds=self.update_interval_seconds * 4)
                _LOGGER.info(
                    "Reduced REST polling to every %d seconds (MQTT provides real-time updates)",
                    self.update_interval_seconds * 4
                )
            else:
                _LOGGER.warning(
                    "MQTT connection failed for device %s, falling back to REST API only",
                    self.device_sn
                )
                self._mqtt_connected = False
                self._use_mqtt = False
                
        except Exception as err:
            _LOGGER.error("Error setting up MQTT for device %s: %s", self.device_sn, err)
            self._mqtt_connected = False
            self._use_mqtt = False

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        if self._mqtt_client:
            await self._mqtt_client.async_disconnect()
            self._mqtt_client = None

    def _handle_mqtt_message(self, payload: dict[str, Any]) -> None:
        """Handle MQTT message from device.
        
        Args:
            payload: MQTT message payload (already extracted from quota topic params)
        """
        try:
            # MQTT client already extracts params from quota topic
            # So payload here is the actual device data
            mqtt_data = payload
            
            # Merge MQTT data with existing data
            self._mqtt_data.update(mqtt_data)
            
            # Schedule update in Home Assistant event loop
            # MQTT callback runs in different thread, so we need to schedule it properly
            merged_data = self._merge_data()
            
            # Schedule async update in HA event loop from MQTT thread
            # Use hass.async_add_job which is thread-safe and handles async functions correctly
            # This ensures the async function runs in the correct event loop
            self.hass.async_add_job(self.async_set_updated_data, merged_data)
            
            _LOGGER.debug(
                "Processed MQTT update for device %s, scheduling coordinator update",
                self.device_sn
            )
            
        except Exception as err:
            _LOGGER.error("Error handling MQTT message: %s", err)

    def _merge_data(self) -> dict[str, Any]:
        """Merge REST API and MQTT data.
        
        Priority: MQTT data > REST data (MQTT is more real-time)
        
        Returns:
            Merged data dictionary
        """
        # Start with REST data
        merged = dict(self._last_data)
        
        # Overlay MQTT data (more recent)
        merged.update(self._mqtt_data)
        
        return merged

    async def _async_wake_device(self) -> None:
        """Wake up device before requesting data.
        
        Some EcoFlow devices go to sleep and don't respond to API requests
        until "woken up" by sending a request. This method sends a wake-up
        request to ensure device is responsive before fetching actual data.
        
        If MQTT is active and receiving data, wake-up may not be needed.
        Otherwise uses REST API wake-up (most reliable method).
        """
        # If MQTT is active and we have recent data, device is likely awake
        # Skip wake-up to avoid unnecessary requests
        if self._mqtt_connected and self._mqtt_data:
            _LOGGER.debug("MQTT active with data for %s, skipping wake-up", self.device_sn)
            return
        
        # Device might be sleeping - send wake-up request via REST API
        try:
            # Send a wake-up request (first quota request to wake device)
            # This is a lightweight operation that helps wake sleeping devices
            await self.client.get_device_quota(self.device_sn)
            _LOGGER.debug("Wake-up request sent via REST for %s", self.device_sn)
            # Small delay to allow device to wake up and process the request
            await asyncio.sleep(0.5)
        except Exception as err:
            # Don't fail on wake-up errors, just log them
            # Device might already be awake or wake-up might not be needed
            _LOGGER.debug("Wake-up request failed (non-critical): %s", err)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API (and merge with MQTT if available).
        
        Returns:
            Device data dictionary
            
        Raises:
            UpdateFailed: If data fetch fails
        """
        try:
            # Wake up device before requesting data
            # This helps with devices that go to sleep and don't respond
            # until woken up by a request or command
            await self._async_wake_device()
            
            # Always fetch from REST API (but less frequently if MQTT is active)
            rest_data = await self.client.get_device_quota(self.device_sn)
            _LOGGER.debug("Received REST data for %s: %s", self.device_sn, rest_data)
            
            # Store last successful REST data
            self._last_data = rest_data
            
            # If MQTT is active, merge data
            if self._use_mqtt and self._mqtt_connected:
                return self._merge_data()
            else:
                # REST only
                return rest_data
            
        except EcoFlowApiError as err:
            _LOGGER.error("Error fetching REST data for %s: %s", self.device_sn, err)
            
            # If MQTT is available, use MQTT data only
            if self._use_mqtt and self._mqtt_connected and self._mqtt_data:
                _LOGGER.info("Using MQTT data only (REST API failed)")
                return self._merge_data()
            
            raise UpdateFailed(f"Error fetching data: {err}") from err

