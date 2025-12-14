"""Config flow for EcoFlow API integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .api import EcoFlowApiClient, EcoFlowApiError, EcoFlowAuthError
from .const import (
    CONF_ACCESS_KEY,
    CONF_DEVICE_SN,
    CONF_DEVICE_TYPE,
    CONF_MQTT_ENABLED,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_SECRET_KEY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_TYPE_DELTA_PRO_3,
    DEVICE_TYPES,
    DOMAIN,
    OPTS_DIAGNOSTIC_MODE,
)

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

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
        vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_DELTA_PRO_3): vol.In(DEVICE_TYPES),
    }
)

# Step 3: MQTT configuration (optional)
STEP_MQTT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MQTT_ENABLED, default=False): bool,
        vol.Optional(CONF_MQTT_USERNAME): str,
        vol.Optional(CONF_MQTT_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for EcoFlow API.

    This config flow allows users to:
    1. Enter their EcoFlow Developer API credentials
    2. Automatically discover devices or enter manually
    3. Select device type
    """

    DOMAIN = DOMAIN
    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._access_key: str | None = None
        self._secret_key: str | None = None
        self._devices: list[dict[str, Any]] = []
        self._client: EcoFlowApiClient | None = None

    async def async_step_user(self, _user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step - choose setup method.

        Args:
            user_input: User provided data

        Returns:
            Flow result
        """
        # Show menu to choose between automatic discovery or manual entry
        return self.async_show_menu(
            step_id="user",
            menu_options=["auto_discovery", "manual_entry"],
        )

    async def async_step_auto_discovery(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle automatic device discovery via API.

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
                devices = await client.get_device_list()

                self._access_key = user_input[CONF_ACCESS_KEY]
                self._secret_key = user_input[CONF_SECRET_KEY]
                self._client = client
                self._devices = devices if isinstance(devices, list) else []

                _LOGGER.info("Found %d devices: %s", len(self._devices), self._devices)

                if self._devices:
                    # Proceed to device selection
                    return await self.async_step_select_device()
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
            step_id="auto_discovery",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer-eu.ecoflow.com/",
            },
        )

    async def async_step_manual_entry(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual entry of all device information.

        Args:
            user_input: User provided data

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        # Schema for manual entry - all fields at once
        manual_schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_DEVICE_SN): str,
                vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_DELTA_PRO_3): vol.In(DEVICE_TYPES),
            }
        )

        if user_input is not None:
            try:
                access_key = user_input[CONF_ACCESS_KEY]
                secret_key = user_input[CONF_SECRET_KEY]
                device_sn = user_input[CONF_DEVICE_SN]
                device_type = user_input[CONF_DEVICE_TYPE]

                _LOGGER.info("Manual entry: SN=%s, Type=%s", device_sn, device_type)

                # Check if device is already configured
                await self.async_set_unique_id(device_sn)
                self._abort_if_unique_id_configured()

                # Test API credentials
                session = async_get_clientsession(self.hass)
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=session,
                )

                # Try to verify device access (non-blocking)
                try:
                    quota = await client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
                except EcoFlowApiError as err:
                    _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)

                # Create entry
                device_name = DEVICE_TYPES.get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: access_key,
                        CONF_SECRET_KEY: secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                    },
                )

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
            step_id="manual_entry",
            data_schema=manual_schema,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer-eu.ecoflow.com/",
            },
        )

    async def async_step_select_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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

            _LOGGER.info("Selected device: SN=%s, Type=%s", device_sn, device_type)

            # Check if device is already configured
            await self.async_set_unique_id(device_sn)
            self._abort_if_unique_id_configured()

            # Try to verify device access (non-blocking - just warn if fails)
            try:
                if self._client:
                    quota = await self._client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
            except EcoFlowApiError as err:
                _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)
                # Don't set error - allow setup to continue
                # The coordinator will handle verification during runtime

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
                device_options.append(
                    {
                        "value": sn,
                        "label": f"{status} {device_name} ({sn[-4:]})",
                    }
                )

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
                        options=[{"value": k, "label": v} for k, v in DEVICE_TYPES.items()],
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

    async def async_step_manual_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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

            _LOGGER.info("Manual device entry: SN=%s, Type=%s", device_sn, device_type)

            # Check if device is already configured
            await self.async_set_unique_id(device_sn)
            self._abort_if_unique_id_configured()

            # Try to verify device access (non-blocking - just warn if fails)
            try:
                if self._client:
                    quota = await self._client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
            except EcoFlowApiError as err:
                _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)
                # Don't set error - allow setup to continue
                # The coordinator will handle verification during runtime

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

    async def async_step_reauth(self, _entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthorization.

        Args:
            entry_data: Existing entry data

        Returns:
            Flow result
        """
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
                    entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
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

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for EcoFlow API integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        # Store config_entry reference (use private variable to avoid property conflict)
        self._entry = config_entry

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Return config entry."""
        return self._entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current update interval
        current_interval = (
            self.config_entry.options.get(CONF_UPDATE_INTERVAL)
            if self.config_entry.options
            else self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )

        # Get current MQTT settings
        mqtt_enabled = self.config_entry.options.get(CONF_MQTT_ENABLED, False)
        mqtt_username = self.config_entry.options.get(CONF_MQTT_USERNAME, "")
        mqtt_password = self.config_entry.options.get(CONF_MQTT_PASSWORD, "")

        # Get current device options
        diagnostic_mode = self.config_entry.options.get(OPTS_DIAGNOSTIC_MODE, False)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.In(
                        {
                            5: "5 seconds (Fast)",
                            10: "10 seconds",
                            15: "15 seconds (Recommended)",
                            30: "30 seconds",
                            60: "60 seconds (Slow)",
                        }
                    ),
                    vol.Optional(
                        CONF_MQTT_ENABLED,
                        default=mqtt_enabled,
                    ): bool,
                    vol.Optional(
                        CONF_MQTT_USERNAME,
                        description={
                            "suggested_value": mqtt_username,
                            "description": "EcoFlow email OR access_key (empty uses main)",
                        },
                    ): str,
                    vol.Optional(
                        CONF_MQTT_PASSWORD,
                        description={
                            "suggested_value": mqtt_password,
                            "description": "EcoFlow password OR secret_key (empty uses main)",
                        },
                    ): str,
                    vol.Optional(
                        OPTS_DIAGNOSTIC_MODE,
                        default=diagnostic_mode,
                    ): bool,
                }
            ),
        )
