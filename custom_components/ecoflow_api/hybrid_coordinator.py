"""Hybrid DataUpdateCoordinator for EcoFlow API (REST + MQTT).

This coordinator combines:
- REST API for device control and fallback polling
- MQTT for real-time sensor updates and additional data
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import EcoFlowApiClient, EcoFlowApiError
from .const import OPTS_VERBOSE_LOGGING
from .coordinator import EcoFlowDataCoordinator
from .data_holder import BoundFifoList
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
        
        # Track last REST update time for interval verification
        self._last_rest_update: float | None = None
        
        # Timer for periodic REST updates (independent of MQTT)
        self._rest_update_timer: asyncio.TimerHandle | None = None
        
        # MQTT messages collection for diagnostic mode
        if self._diagnostic_mode:
            self.mqtt_messages: BoundFifoList[dict[str, Any]] = BoundFifoList(maxlen=20)
        
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
        
        # Start periodic REST updates (independent of MQTT updates)
        # This ensures REST polling happens even when MQTT is updating data
        self._schedule_rest_update()
        
        # Listen for Home Assistant stop event to gracefully shutdown
        self.hass.bus.async_listen_once("homeassistant_stop", self._async_handle_stop)
        
        return True
    
    async def _async_handle_stop(self, event) -> None:
        """Handle Home Assistant stop event.
        
        This ensures MQTT client is properly disconnected before Home Assistant shuts down,
        preventing "Event loop is closed" errors during restart.
        """
        _LOGGER.info("Home Assistant stopping, shutting down MQTT for %s", self.device_sn)
        await self.async_shutdown()

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
                _LOGGER.info(
                    "⚠️ Hybrid mode active: MQTT for real-time updates + REST every %d seconds for all fields",
                    self.update_interval_seconds
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
        # Cancel REST update timer
        if self._rest_update_timer:
            self._rest_update_timer.cancel()
            self._rest_update_timer = None
            
        # Disconnect MQTT
        if self._mqtt_client:
            await self._mqtt_client.async_disconnect()
            self._mqtt_client = None
    
    def _schedule_rest_update(self) -> None:
        """Schedule next REST update.
        
        This runs independently of MQTT updates to ensure periodic REST polling.
        """
        # Cancel any existing timer
        if self._rest_update_timer:
            self._rest_update_timer.cancel()
        
        # Schedule next update - use hass.async_create_task for proper tracking
        async def do_update():
            try:
                await self._do_rest_update()
            except Exception as err:
                _LOGGER.error("Error in scheduled REST update: %s", err)
        
        self._rest_update_timer = self.hass.loop.call_later(
            self.update_interval_seconds,
            lambda: self.hass.async_create_task(do_update())
        )
    
    async def _do_rest_update(self) -> None:
        """Perform REST update and schedule next one."""
        _LOGGER.debug("Executing scheduled REST update")
        try:
            # Force refresh (this calls _async_update_data)
            await self.async_refresh()
        except Exception as err:
            _LOGGER.error("Error during REST update: %s", err)
        finally:
            # Schedule next update
            self._schedule_rest_update()


    def _handle_mqtt_message(self, payload: dict[str, Any]) -> None:
        """Handle MQTT message from device.
        
        Args:
            payload: MQTT message payload (already extracted from quota topic params)
        """
        try:
            # Check if event loop is still running (Home Assistant not shutting down)
            if not self.hass.loop.is_running() or self.hass.loop.is_closed():
                return
            
            # MQTT client already extracts params from quota topic
            # So payload here is the actual device data
            mqtt_data = payload
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            fields_count = len(mqtt_data)
            
            # Log MQTT message with summary (only if verbose logging enabled)
            if self._is_verbose_logging_enabled():
                _LOGGER.info(
                    "⚡ [%s] MQTT message for %s: %d fields updated",
                    timestamp,
                    self.device_sn[-4:],
                    fields_count
                )
                
                # Log which fields were updated (keys only, to avoid spam)
                if fields_count > 0:
                    field_names = list(mqtt_data.keys())
                    if fields_count <= 10:
                        # Show all fields if 10 or less
                        _LOGGER.info("   Fields: %s", ", ".join(field_names))
                    else:
                        # Show first 10 + count
                        _LOGGER.info(
                            "   Fields: %s ... (+%d more)",
                            ", ".join(field_names[:10]),
                            fields_count - 10
                        )
            
            # Store MQTT message in diagnostic mode
            if self._diagnostic_mode:
                self.mqtt_messages.append({
                    "timestamp": time.time(),
                    "device_sn": self.device_sn,
                    "payload": mqtt_data,
                })
            
            # Track what changed in MQTT data
            old_mqtt_field_count = len(self._mqtt_data)
            
            # Merge MQTT data with existing data
            self._mqtt_data.update(mqtt_data)
            
            new_mqtt_field_count = len(self._mqtt_data)
            
            if self._is_verbose_logging_enabled() and new_mqtt_field_count > old_mqtt_field_count:
                _LOGGER.info(
                    "   Total MQTT fields: %d → %d (+%d new)",
                    old_mqtt_field_count,
                    new_mqtt_field_count,
                    new_mqtt_field_count - old_mqtt_field_count
                )
            
            # Schedule update in Home Assistant event loop
            # MQTT callback runs in different thread, so we need to schedule it properly
            merged_data = self._merge_data()
            
            # Schedule update in HA event loop from MQTT thread
            # async_set_updated_data is a sync method (despite the async_ prefix)
            # Use call_soon_threadsafe to schedule it in the correct event loop
            self.hass.loop.call_soon_threadsafe(lambda: self.async_set_updated_data(merged_data))
            
        except RuntimeError:
            # Event loop closed during shutdown - ignore silently
            pass
        except Exception as err:
            _LOGGER.error("Error handling MQTT message: %s", err)

    def _is_verbose_logging_enabled(self) -> bool:
        """Check if verbose logging is enabled in options."""
        if not self.config_entry:
            # No config entry - always show logs for debugging
            return True
        
        # Check if option exists in options
        verbose = self.config_entry.options.get(OPTS_VERBOSE_LOGGING, False)
        
        # Debug: log once what we found
        if not hasattr(self, "_logged_verbose_state"):
            self._logged_verbose_state = True
            _LOGGER.info(
                "Verbose logging is %s for %s (config_entry=%s, options=%s)",
                "ENABLED" if verbose else "DISABLED",
                self.device_sn[-4:],
                "present" if self.config_entry else "missing",
                self.config_entry.options if self.config_entry else None
            )
        
        return verbose

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
        
        EcoFlow devices often go to sleep when:
        - App is closed
        - No activity for some time
        - Screen is off
        
        When sleeping, devices may:
        - Stop sending MQTT updates for some fields
        - Return stale data via REST API
        - Not update timestamps
        
        Solution: Always wake device before REST polling to ensure fresh data.
        """
        # Always wake device before REST polling
        # This ensures we get fresh data even if device was sleeping
        try:
            # Send wake-up request - this wakes the device
            await self.client.get_device_quota(self.device_sn)
            
            # Short delay to allow device to wake up and prepare data
            await asyncio.sleep(1.0)
                
        except Exception:
            # Don't fail on wake-up errors - device might already be awake
            pass
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API (and merge with MQTT if available).
        
        Returns:
            Device data dictionary
            
        Raises:
            UpdateFailed: If data fetch fails
        """
        try:
            # Calculate time since last REST update
            current_time = time.time()
            time_since_last = None
            if self._last_rest_update:
                time_since_last = current_time - self._last_rest_update
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if self._is_verbose_logging_enabled():
                _LOGGER.info(
                    "🔄 [%s] REST UPDATE TRIGGERED for %s (configured_interval=%ds, actual_since_last=%.1fs, mqtt=%s)",
                    timestamp,
                    self.device_sn[-4:],  # Only last 4 chars of SN
                    self.update_interval_seconds,
                    time_since_last if time_since_last else 0,
                    "ON" if self._mqtt_connected else "OFF"
                )
            
            # Wake up device before requesting data
            # This helps with devices that go to sleep and don't respond
            # until woken up by a request or command
            await self._async_wake_device()
            
            # Fetch from REST API
            if self._is_verbose_logging_enabled():
                _LOGGER.info("🌐 [%s] Fetching REST data for %s...", timestamp, self.device_sn[-4:])
            rest_data = await self.client.get_device_quota(self.device_sn)
            
            rest_field_count = len(rest_data)
            
            # Compare with previous data to find changed fields
            changed_fields = []
            if self._last_data is not None:  # Fix: use 'is not None' to handle empty dict
                # Check for changed or new fields
                for key, new_value in rest_data.items():
                    old_value = self._last_data.get(key)
                    if old_value != new_value:
                        changed_fields.append((key, old_value, new_value))
                
                # Check for removed fields (existed before but not now)
                for key in self._last_data:
                    if key not in rest_data:
                        changed_fields.append((key, self._last_data[key], None))
            
            if self._is_verbose_logging_enabled():
                _LOGGER.info(
                    "✅ [%s] REST update for %s: received %d fields, %d changed",
                    timestamp,
                    self.device_sn[-4:],
                    rest_field_count,
                    len(changed_fields)
                )
                
                # Log changed fields - show ALL changes with readable formatting
                if changed_fields:
                    _LOGGER.info(
                        "📊 [%s] Changed fields (%d total):",
                        timestamp,
                        len(changed_fields)
                    )
                    for key, old_val, new_val in changed_fields:
                        # Format values for readability
                        old_str = str(old_val)[:50] if old_val is not None else "None"
                        new_str = str(new_val)[:50] if new_val is not None else "None"
                        _LOGGER.info(
                            "   • %s: %s → %s",
                            key,
                            old_str,
                            new_str
                        )
                else:
                    _LOGGER.info(
                        "📊 [%s] No changes detected (device in stable state)",
                        timestamp
                    )
            
            # Update last REST update timestamp
            self._last_rest_update = current_time
            
            # Store last successful REST data
            self._last_data = rest_data
            
            # If MQTT is active, merge data
            if self._use_mqtt and self._mqtt_connected:
                merged = self._merge_data()
                mqtt_field_count = len(self._mqtt_data)
                total_fields = len(merged)
                if self._is_verbose_logging_enabled():
                    _LOGGER.info(
                        "🔀 [%s] Merged data for %s: REST=%d + MQTT=%d = Total=%d unique fields",
                        timestamp,
                        self.device_sn[-4:],
                        rest_field_count,
                        mqtt_field_count,
                        total_fields
                    )
                return merged
            else:
                # REST only
                if self._is_verbose_logging_enabled():
                    _LOGGER.info(
                        "📡 [%s] Using REST data only for %s (%d fields)",
                        timestamp,
                        self.device_sn[-4:],
                        rest_field_count
                    )
                return rest_data
            
        except EcoFlowApiError as err:
            _LOGGER.error("Error fetching REST data for %s: %s", self.device_sn, err)
            
            # If MQTT is available, use MQTT data only
            if self._use_mqtt and self._mqtt_connected and self._mqtt_data:
                _LOGGER.info("Using MQTT data only (REST API failed)")
                return self._merge_data()
            
            raise UpdateFailed(f"Error fetching data: {err}") from err

