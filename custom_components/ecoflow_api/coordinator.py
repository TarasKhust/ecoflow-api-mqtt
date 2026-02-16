"""DataUpdateCoordinator for EcoFlow API."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EcoFlowApiClient, EcoFlowApiError
from .const import DOMAIN, OPTS_DIAGNOSTIC_MODE
from .data_holder import BoundFifoList

_LOGGER = logging.getLogger(__name__)


class EcoFlowDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching EcoFlow data from API.

    This coordinator handles:
    - Periodic data updates from the EcoFlow API
    - Caching of device data
    - Error handling and retry logic
    - Providing methods for setting device parameters
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: EcoFlowApiClient,
        device_sn: str,
        device_type: str,
        update_interval: int = 15,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            client: EcoFlow API client
            device_sn: Device serial number
            device_type: Device type identifier
            update_interval: Update interval in seconds (default: 15)
            config_entry: Config entry reference
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_sn}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        self.api_client = client  # Alias for compatibility
        self.device_sn = device_sn
        self.device_type = device_type
        self.update_interval_seconds = update_interval
        self._last_data: dict[str, Any] = {}
        if config_entry:
            self.config_entry = config_entry

        # Diagnostic mode data collection (only if enabled)
        self._diagnostic_mode = False
        if config_entry:
            self._diagnostic_mode = config_entry.options.get(OPTS_DIAGNOSTIC_MODE, False)

        if self._diagnostic_mode:
            self.rest_requests: BoundFifoList[dict[str, Any]] = BoundFifoList(maxlen=20)
            self.set_commands: BoundFifoList[dict[str, Any]] = BoundFifoList(maxlen=20)
            self.set_replies: BoundFifoList[dict[str, Any]] = BoundFifoList(maxlen=20)

        # Track if we've logged connection success (to avoid spam)
        self._logged_rest_success = False

    async def _async_wake_device(self) -> None:
        """Wake up device before requesting data.

        Some EcoFlow devices go to sleep and don't respond to API requests
        until "woken up" by sending a command or request.
        This method sends a wake-up request to ensure device is responsive.
        """
        try:
            # Send a wake-up request (first quota request to wake device)
            # This is a lightweight operation that helps wake sleeping devices
            await self.client.get_device_quota(self.device_sn)
            # Small delay to allow device to wake up
            await asyncio.sleep(0.5)
        except Exception:  # noqa: S110
            # Don't fail on wake-up errors - device might already be awake
            pass

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.

        Returns:
            Device data dictionary

        Raises:
            UpdateFailed: If data fetch fails
        """
        try:
            # Debug logging (only if logger level is DEBUG)
            if _LOGGER.isEnabledFor(logging.DEBUG):
                timestamp = datetime.now().strftime("%H:%M:%S")
                _LOGGER.debug(
                    "🔄 [%s] REST UPDATE for %s (interval=%ds, mode=REST-only)",
                    timestamp,
                    self.device_sn[-4:],
                    self.update_interval_seconds,
                )

            # Wake up device before requesting data
            await self._async_wake_device()

            # Fetch device data
            data = await self.client.get_device_quota(self.device_sn)

            # Log success only once (first successful request)
            if not self._logged_rest_success:
                self._logged_rest_success = True
                _LOGGER.info(
                    "✅ REST API connected for device %s (REST-only mode, update interval: %ds)",
                    self.device_sn[-4:],
                    self.update_interval_seconds,
                )

            # Debug: Log data details
            if _LOGGER.isEnabledFor(logging.DEBUG):
                timestamp = datetime.now().strftime("%H:%M:%S")
                field_count = len(data)

                # Compare with previous data
                changed_fields = []
                if self._last_data is not None:
                    for key, new_value in data.items():
                        old_value = self._last_data.get(key)
                        if old_value != new_value:
                            changed_fields.append((key, old_value, new_value))
                    changed_fields.extend(
                        (key, self._last_data[key], None) for key in self._last_data if key not in data
                    )

                _LOGGER.debug(
                    "✅ [%s] REST update for %s: received %d fields, %d changed",
                    timestamp,
                    self.device_sn[-4:],
                    field_count,
                    len(changed_fields),
                )

                if changed_fields:
                    _LOGGER.debug("📊 [%s] Changed fields (%d total):", timestamp, len(changed_fields))
                    for key, old_val, new_val in changed_fields[:10]:  # Show max 10
                        old_str = str(old_val)[:50] if old_val is not None else "None"
                        new_str = str(new_val)[:50] if new_val is not None else "None"
                        _LOGGER.debug("   • %s: %s → %s", key, old_str, new_str)
                    if len(changed_fields) > 10:
                        _LOGGER.debug("   ... and %d more", len(changed_fields) - 10)

            # Store diagnostic data if enabled
            if self._diagnostic_mode:
                self.rest_requests.append(
                    {
                        "timestamp": time.time(),
                        "device_sn": self.device_sn,
                        "response": data,
                    }
                )

            # Store last successful data
            self._last_data = data
            return data

        except EcoFlowApiError as err:
            _LOGGER.error("Error fetching data for %s: %s", self.device_sn, err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for device registry."""
        from .devices import get_profile

        profile = get_profile(self.device_type)
        display_name = profile.display_name if profile else self.device_type

        return {
            "identifiers": {(DOMAIN, self.device_sn)},
            "name": f"EcoFlow {display_name}",
            "manufacturer": "EcoFlow",
            "model": display_name,
            "serial_number": self.device_sn,
        }

    async def async_send_command(self, command: dict) -> bool:
        """Send command to device via REST API.

        Base implementation uses REST API only.
        HybridCoordinator overrides this to try MQTT first with REST fallback.

        Raises exceptions on failure so entity code can handle them properly.

        Args:
            command: Command payload with params

        Returns:
            True if command sent successfully
        """
        _LOGGER.debug(
            "Sending command via REST API for %s: params=%s",
            self.device_sn[-4:],
            command.get("params", {}),
        )
        result = await self.client.set_device_quota(
            device_sn=self.device_sn,
            cmd_code=command,
        )
        _LOGGER.debug(
            "Command sent via REST API for %s: response=%s",
            self.device_sn[-4:],
            result,
        )
        return True

    async def async_set_update_interval(self, interval_seconds: int) -> None:
        """Set the update interval dynamically.

        Args:
            interval_seconds: New update interval in seconds
        """
        _LOGGER.info(
            "Changing update interval from %d to %d seconds for %s",
            self.update_interval_seconds,
            interval_seconds,
            self.device_sn,
        )
        self.update_interval_seconds = interval_seconds
        self.update_interval = timedelta(seconds=interval_seconds)

        # Update config entry options to persist the change
        if self.config_entry:
            from .const import CONF_UPDATE_INTERVAL

            new_options = dict(self.config_entry.options)
            new_options[CONF_UPDATE_INTERVAL] = interval_seconds
            self.hass.config_entries.async_update_entry(self.config_entry, options=new_options)

        # Force immediate refresh with new interval
        await self.async_request_refresh()
