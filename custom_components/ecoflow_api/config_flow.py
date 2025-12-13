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
            # Validate and store API credentials
            access_key = user_input[CONF_ACCESS_KEY]
            secret_key = user_input[CONF_SECRET_KEY]

            # Test API connection
            try:
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=async_get_clientsession(self.hass),
                )

                # Test connection
                if await client.test_connection():
                    self._access_key = access_key
                    self._secret_key = secret_key
                    self._client = client

                    # Discover devices
                    await self._discover_devices()

                    if self._devices:
                        # Show device selection
                        return await self.async_step_select_device()
                    else:
                        # No devices found, show manual entry
                        errors["base"] = "no_devices"
                        return self.async_show_form(
                            step_id="auto_discovery",
                            data_schema=STEP_CREDENTIALS_SCHEMA,
                            errors=errors,
                        )
                else:
                    errors["base"] = "invalid_auth"

            except EcoFlowAuthError:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during API connection: %s", err)
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="auto_discovery",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
        )

    async def async_step_manual_entry(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual entry of all device information.

        Args:
            user_input: User provided data

        Returns:
            Flow result
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate and store API credentials
            access_key = user_input[CONF_ACCESS_KEY]
            secret_key = user_input[CONF_SECRET_KEY]
            device_sn = user_input[CONF_DEVICE_SN]
            device_type = user_input[CONF_DEVICE_TYPE]

            # Test API connection
            try:
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=async_get_clientsession(self.hass),
                )

                # Test connection
                if await client.test_connection():
                    # Verify device exists
                    try:
                        quota = await client.get_device_quota(device_sn)
                        _LOGGER.info("Device verification successful: %s", quota)
                    except EcoFlowApiError as err:
                        _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)

                    # Create entry
                    device_name = DEVICE_TYPES.get(device_type, device_type)
                    title = f"EcoFlow {device_name} ({device_sn[-4:]})"

                    data = {
                        CONF_ACCESS_KEY: access_key,
                        CONF_SECRET_KEY: secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                    }

                    # Show MQTT configuration step
                    return await self.async_step_mqtt_config(data, title)
                else:
                    errors["base"] = "invalid_auth"

            except EcoFlowAuthError:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during API connection: %s", err)
                errors["base"] = "unknown"

        # Show form
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_DEVICE_SN): str,
                vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_DELTA_PRO_3): vol.In(DEVICE_TYPES),
            }
        )

        return self.async_show_form(
            step_id="manual_entry",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_select_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle device selection from discovered devices.

        Args:
            user_input: User provided data

        Returns:
            Flow result
        """
        if user_input is not None:
            device_sn = user_input[CONF_DEVICE_SN]
            device_type = user_input[CONF_DEVICE_TYPE]

            # Verify device exists
            try:
                if self._client:
                    quota = await self._client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
            except EcoFlowApiError as err:
                _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)
                # Don't set error - allow setup to continue
                # The coordinator will handle verification during runtime

            # Create entry
            device_name = DEVICE_TYPES.get(device_type, device_type)
            title = f"EcoFlow {device_name} ({device_sn[-4:]})"

            data = {
                CONF_ACCESS_KEY: self._access_key,
                CONF_SECRET_KEY: self._secret_key,
                CONF_DEVICE_SN: device_sn,
                CONF_DEVICE_TYPE: device_type,
            }

            # Show MQTT configuration step
            return await self.async_step_mqtt_config(data, title)

        # Build device selection schema
        device_options = [
            {"value": device["sn"], "label": f"{device['name']} ({device['sn'][-4:]})"}
            for device in self._devices
        ]

        schema = vol.Schema(
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
            data_schema=schema,
            errors={},
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

            # Verify device exists
            try:
                if self._client:
                    quota = await self._client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
            except EcoFlowApiError as err:
                _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)
                # Don't set error - allow setup to continue
                # The coordinator will handle verification during runtime

            # Create entry
            device_name = DEVICE_TYPES.get(device_type, device_type)
            title = f"EcoFlow {device_name} ({device_sn[-4:]})"

            data = {
                CONF_ACCESS_KEY: self._access_key,
                CONF_SECRET_KEY: self._secret_key,
                CONF_DEVICE_SN: device_sn,
                CONF_DEVICE_TYPE: device_type,
            }

            # Show MQTT configuration step
            return await self.async_step_mqtt_config(data, title)

        # Show manual device entry form
        return self.async_show_form(
            step_id="manual_device",
            data_schema=STEP_MANUAL_DEVICE_SCHEMA,
            errors=errors,
        )

    async def async_step_mqtt_config(self, data: dict[str, Any], title: str) -> FlowResult:
        """Handle MQTT configuration step.

        Args:
            data: Existing configuration data
            title: Entry title

        Returns:
            Flow result
        """
        return await self.async_step_mqtt(data, title)

    async def async_step_mqtt(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle MQTT configuration.

        Args:
            user_input: User provided data

        Returns:
            Flow result
        """
        if user_input is not None:
            # MQTT configuration completed, create entry
            mqtt_enabled = user_input.get(CONF_MQTT_ENABLED, False)
            mqtt_username = user_input.get(CONF_MQTT_USERNAME) if mqtt_enabled else None
            mqtt_password = user_input.get(CONF_MQTT_PASSWORD) if mqtt_enabled else None

            # Get existing data from context
            existing_data = self.context.get("data", {})
            data = {
                **existing_data,
                CONF_MQTT_ENABLED: mqtt_enabled,
                CONF_MQTT_USERNAME: mqtt_username,
                CONF_MQTT_PASSWORD: mqtt_password,
            }

            # Create entry
            device_sn = data[CONF_DEVICE_SN]
            device_type = data[CONF_DEVICE_TYPE]
            device_name = DEVICE_TYPES.get(device_type, device_type)
            title = f"EcoFlow {device_name} ({device_sn[-4:]})"

            return self.async_create_entry(title=title, data=data)

        # Show MQTT configuration form
        return self.async_show_form(
            step_id="mqtt",
            data_schema=STEP_MQTT_SCHEMA,
            errors={},
        )

    async def async_step_reauth(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle reauthentication.

        Args:
            user_input: User provided data

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
            access_key = user_input[CONF_ACCESS_KEY]
            secret_key = user_input[CONF_SECRET_KEY]

            try:
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=async_get_clientsession(self.hass),
                )

                if await client.test_connection():
                    # Update the config entry with new credentials
                    entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
                    if entry:
                        self.hass.config_entries.async_update_entry(
                            entry,
                            data={
                                **entry.data,
                                CONF_ACCESS_KEY: access_key,
                                CONF_SECRET_KEY: secret_key,
                            },
                        )
                    return self.async_abort(reason="reauth_successful")
                else:
                    errors["base"] = "invalid_auth"

            except EcoFlowAuthError:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.error("Unexpected error during reauth: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
        )

    async def _discover_devices(self) -> None:
        """Discover devices via API."""
        if not self._client:
            return

        try:
            devices = await self._client.get_devices()
            self._devices = devices
            _LOGGER.info("Discovered %d devices", len(devices))
        except Exception as err:
            _LOGGER.error("Error discovering devices: %s", err)
            self._devices = []


class EcoFlowOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for EcoFlow API."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = (
            self.config_entry.options.get(CONF_UPDATE_INTERVAL)
            if self.config_entry.options
            else self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )

        # Get current MQTT settings
        mqtt_enabled = (
            self.config_entry.options.get(CONF_MQTT_ENABLED)
            if self.config_entry.options
            else self.config_entry.data.get(CONF_MQTT_ENABLED, False)
        )
        mqtt_username = (
            self.config_entry.options.get(CONF_MQTT_USERNAME)
            if self.config_entry.options
            else self.config_entry.data.get(CONF_MQTT_USERNAME)
        )
        mqtt_password = (
            self.config_entry.options.get(CONF_MQTT_PASSWORD)
            if self.config_entry.options
            else self.config_entry.data.get(CONF_MQTT_PASSWORD)
        )

        diagnostic_mode = (
            self.config_entry.options.get(OPTS_DIAGNOSTIC_MODE, False)
            if self.config_entry.options
            else False
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current_interval,
                ): int,
                vol.Optional(
                    CONF_MQTT_ENABLED,
                    default=mqtt_enabled,
                ): bool,
                vol.Optional(
                    CONF_MQTT_USERNAME,
                    default=mqtt_username or "",
                ): str,
                vol.Optional(
                    CONF_MQTT_PASSWORD,
                    default=mqtt_password or "",
                ): str,
                vol.Optional(
                    OPTS_DIAGNOSTIC_MODE,
                    default=diagnostic_mode,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
