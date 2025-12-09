"""DataUpdateCoordinator for EcoFlow API."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EcoFlowApiClient, EcoFlowApiError
from .const import DOMAIN

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
    ) -> None:
        """Initialize coordinator.
        
        Args:
            hass: Home Assistant instance
            client: EcoFlow API client
            device_sn: Device serial number
            device_type: Device type identifier
            update_interval: Update interval in seconds (default: 15)
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.
        
        Returns:
            Device data dictionary
            
        Raises:
            UpdateFailed: If data fetch fails
        """
        try:
            data = await self.client.get_device_quota(self.device_sn)
            _LOGGER.debug("Received data for %s: %s", self.device_sn, data)
            
            # Store last successful data
            self._last_data = data
            return data
            
        except EcoFlowApiError as err:
            _LOGGER.error("Error fetching data for %s: %s", self.device_sn, err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for device registry."""
        from .const import DEVICE_TYPES
        
        return {
            "identifiers": {(DOMAIN, self.device_sn)},
            "name": f"EcoFlow {DEVICE_TYPES.get(self.device_type, self.device_type)}",
            "manufacturer": "EcoFlow",
            "model": DEVICE_TYPES.get(self.device_type, self.device_type),
            "serial_number": self.device_sn,
        }

    # Command methods for Delta Pro 3
    
    async def async_set_ac_charging_power(self, power: int) -> None:
        """Set AC charging power.
        
        Args:
            power: Charging power in watts (200-3000)
        """
        try:
            _LOGGER.info("Setting AC charging power to %dW for %s", power, self.device_sn)
            await self.client.set_ac_charging_power(self.device_sn, power)
            # Force refresh to get updated state
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set AC charging power: %s", err)
            raise

    async def async_set_max_charge_level(self, level: int) -> None:
        """Set maximum charge level.
        
        Args:
            level: Max charge level (50-100%)
        """
        try:
            _LOGGER.info("Setting max charge level to %d%% for %s", level, self.device_sn)
            await self.client.set_charge_levels(self.device_sn, max_charge=level)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set max charge level: %s", err)
            raise

    async def async_set_min_discharge_level(self, level: int) -> None:
        """Set minimum discharge level.
        
        Args:
            level: Min discharge level (0-30%)
        """
        try:
            _LOGGER.info("Setting min discharge level to %d%% for %s", level, self.device_sn)
            await self.client.set_charge_levels(self.device_sn, min_discharge=level)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set min discharge level: %s", err)
            raise

    async def async_set_ac_output(self, enabled: bool) -> None:
        """Set AC output state.
        
        Args:
            enabled: Whether to enable AC output
        """
        try:
            _LOGGER.info("Setting AC output to %s for %s", enabled, self.device_sn)
            await self.client.set_ac_output(self.device_sn, enabled)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set AC output: %s", err)
            raise

    async def async_set_dc_output(self, enabled: bool) -> None:
        """Set DC output state.
        
        Args:
            enabled: Whether to enable DC output
        """
        try:
            _LOGGER.info("Setting DC output to %s for %s", enabled, self.device_sn)
            await self.client.set_dc_output(self.device_sn, enabled)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set DC output: %s", err)
            raise

    async def async_set_12v_dc_output(self, enabled: bool) -> None:
        """Set 12V DC output state.
        
        Args:
            enabled: Whether to enable 12V DC output
        """
        try:
            _LOGGER.info("Setting 12V DC output to %s for %s", enabled, self.device_sn)
            await self.client.set_12v_dc_output(self.device_sn, enabled)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set 12V DC output: %s", err)
            raise

    async def async_set_beep(self, enabled: bool) -> None:
        """Set beep state.
        
        Args:
            enabled: Whether to enable beep
        """
        try:
            _LOGGER.info("Setting beep to %s for %s", enabled, self.device_sn)
            await self.client.set_beep(self.device_sn, enabled)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set beep: %s", err)
            raise

    async def async_set_x_boost(self, enabled: bool) -> None:
        """Set X-Boost state.
        
        Args:
            enabled: Whether to enable X-Boost
        """
        try:
            _LOGGER.info("Setting X-Boost to %s for %s", enabled, self.device_sn)
            await self.client.set_x_boost(self.device_sn, enabled)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set X-Boost: %s", err)
            raise

    async def async_set_ac_standby_time(self, minutes: int) -> None:
        """Set AC standby time.
        
        Args:
            minutes: Standby time in minutes (0 = never)
        """
        try:
            _LOGGER.info("Setting AC standby time to %d min for %s", minutes, self.device_sn)
            await self.client.set_ac_standby_time(self.device_sn, minutes)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set AC standby time: %s", err)
            raise

    async def async_set_dc_standby_time(self, minutes: int) -> None:
        """Set DC standby time.
        
        Args:
            minutes: Standby time in minutes (0 = never)
        """
        try:
            _LOGGER.info("Setting DC standby time to %d min for %s", minutes, self.device_sn)
            await self.client.set_dc_standby_time(self.device_sn, minutes)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set DC standby time: %s", err)
            raise

    async def async_set_lcd_standby_time(self, seconds: int) -> None:
        """Set LCD/Screen standby time.
        
        Args:
            seconds: Standby time in seconds (0 = never)
        """
        try:
            _LOGGER.info("Setting LCD standby time to %d sec for %s", seconds, self.device_sn)
            await self.client.set_lcd_standby_time(self.device_sn, seconds)
            await self.async_request_refresh()
        except EcoFlowApiError as err:
            _LOGGER.error("Failed to set LCD standby time: %s", err)
            raise


