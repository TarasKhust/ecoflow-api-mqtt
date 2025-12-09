"""Config flow for EcoFlow API integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import EcoFlowApiClient, EcoFlowApiError, EcoFlowAuthError
from .const import (
    DOMAIN,
    CONF_ACCESS_KEY,
    CONF_SECRET_KEY,
    CONF_DEVICE_SN,
    CONF_DEVICE_TYPE,
    DEVICE_TYPES,
    DEVICE_TYPE_DELTA_PRO_3,
)

_LOGGER = logging.getLogger(__name__)

# Step 1: API credentials
STEP_CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_KEY): str,
        vol.Required(CONF_SECRET_KEY): str,
    }
)

# Step 2: Manual device entry (fallback)
STEP_MANUAL_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_SN): str,
        vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_DELTA_PRO_3): vol.In(
            DEVICE_TYPES
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EcoFlow API.
    
    This config flow allows users to:
    1. Enter their EcoFlow Developer API credentials
    2. Automatically discover devices or enter manually
    3. Select device type
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._access_key: str | None = None
        self._secret_key: str | None = None
        self._devices: list[dict[str, Any]] = []
        self._client: EcoFlowApiClient | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - API credentials.
        
        Args:
            user_input: User provided data
            
        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = EcoFlowApiClient(
                    access_key=user_input[CONF_ACCESS_KEY],
                    secret_key=user_input[CONF_SECRET_KEY],
                    session=session,
                )

                # Test connection and get device list
                _LOGGER.debug("Testing API connection...")
                devices = await client.get_device_list()
                
                self._access_key = user_input[CONF_ACCESS_KEY]
                self._secret_key = user_input[CONF_SECRET_KEY]
                self._client = client
                self._devices = devices if isinstance(devices, list) else []
                
                _LOGGER.info("Found %d devices", len(self._devices))
                
                if self._devices:
                    # Proceed to device selection
                    return await self.async_step_select_device()
                else:
                    # No devices found, allow manual entry
                    return await self.async_step_manual_device()

            except EcoFlowAuthError as err:
                _LOGGER.error("Authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except EcoFlowApiError as err:
                _LOGGER.error("API error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer-eu.ecoflow.com/",
            },
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection from discovered devices.
        
        Args:
            user_input: User provided data
            
        Returns:
            Flow result
        """
        errors: dict[str, str] = {}
        
        if user_input is not None:
            device_sn = user_input[CONF_DEVICE_SN]
            device_type = user_input.get(CONF_DEVICE_TYPE, DEVICE_TYPE_DELTA_PRO_3)
            
            # Check if device is already configured
            await self.async_set_unique_id(device_sn)
            self._abort_if_unique_id_configured()
            
            # Verify device access
            try:
                if self._client:
                    await self._client.get_device_quota(device_sn)
            except EcoFlowApiError as err:
                _LOGGER.error("Device verification failed: %s", err)
                errors["base"] = "invalid_device"
            
            if not errors:
                device_name = DEVICE_TYPES.get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: self._access_key,
                        CONF_SECRET_KEY: self._secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                    },
                )
        
        # Build device options for selector
        device_options = []
        for device in self._devices:
            sn = device.get("sn", device.get("deviceSn", ""))
            device_name = device.get("deviceName", device.get("name", sn))
            online = device.get("online", device.get("isOnline", False))
            status = "🟢" if online else "🔴"
            
            if sn:
                device_options.append({
                    "value": sn,
                    "label": f"{status} {device_name} ({sn[-4:]})",
                })
        
        # If no valid devices, go to manual entry
        if not device_options:
            return await self.async_step_manual_device()
        
        device_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_SN): SelectSelector(
                    SelectSelectorConfig(
                        options=device_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_DELTA_PRO_3): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": k, "label": v}
                            for k, v in DEVICE_TYPES.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        
        return self.async_show_form(
            step_id="select_device",
            data_schema=device_schema,
            errors=errors,
        )

    async def async_step_manual_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual device entry.
        
        Args:
            user_input: User provided data
            
        Returns:
            Flow result
        """
        errors: dict[str, str] = {}
        
        if user_input is not None:
            device_sn = user_input[CONF_DEVICE_SN]
            device_type = user_input[CONF_DEVICE_TYPE]
            
            # Check if device is already configured
            await self.async_set_unique_id(device_sn)
            self._abort_if_unique_id_configured()
            
            # Verify device access
            try:
                if self._client:
                    await self._client.get_device_quota(device_sn)
            except EcoFlowApiError as err:
                _LOGGER.error("Device verification failed: %s", err)
                errors["base"] = "invalid_device"
            
            if not errors:
                device_name = DEVICE_TYPES.get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: self._access_key,
                        CONF_SECRET_KEY: self._secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                    },
                )
        
        return self.async_show_form(
            step_id="manual_device",
            data_schema=STEP_MANUAL_DEVICE_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauthorization.
        
        Args:
            entry_data: Existing entry data
            
        Returns:
            Flow result
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthorization confirmation.
        
        Args:
            user_input: User provided data
            
        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = EcoFlowApiClient(
                    access_key=user_input[CONF_ACCESS_KEY],
                    secret_key=user_input[CONF_SECRET_KEY],
                    session=session,
                )

                if await client.test_connection():
                    # Update the config entry with new credentials
                    entry = self.hass.config_entries.async_get_entry(
                        self.context["entry_id"]
                    )
                    if entry:
                        self.hass.config_entries.async_update_entry(
                            entry,
                            data={
                                **entry.data,
                                CONF_ACCESS_KEY: user_input[CONF_ACCESS_KEY],
                                CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                            },
                        )
                        await self.hass.config_entries.async_reload(entry.entry_id)
                        return self.async_abort(reason="reauth_successful")
                else:
                    errors["base"] = "invalid_auth"

            except EcoFlowAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_KEY): str,
                    vol.Required(CONF_SECRET_KEY): str,
                }
            ),
            errors=errors,
        )
