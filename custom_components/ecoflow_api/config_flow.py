"""Config flow for EcoFlow API integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import EcoFlowApiClient, EcoFlowApiError, EcoFlowAuthError
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
    OPTS_DIAGNOSTIC_MODE,
    REGION_EU,
    REGIONS,
    JsonVal,
)
from .devices import get_device_types

_LOGGER = logging.getLogger(__name__)

_DEFAULT_DEVICE_TYPE = "delta_pro_3"

# Step 1: API credentials with region selection
STEP_CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default=REGION_EU): vol.In(REGIONS),
        vol.Required(CONF_ACCESS_KEY): str,
        vol.Required(CONF_SECRET_KEY): str,
    }
)

# Step 2: Manual device entry (fallback) - built dynamically in methods
# (can't use get_device_types() at module level due to import order)

# Step 3: MQTT configuration (optional)
STEP_MQTT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MQTT_ENABLED, default=False): bool,
        vol.Optional(CONF_MQTT_USERNAME): str,
        vol.Optional(CONF_MQTT_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EcoFlow API.

    This config flow allows users to:
    1. Enter their EcoFlow Developer API credentials
    2. Automatically discover devices or enter manually
    3. Select device type
    """

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._access_key: str | None = None
        self._secret_key: str | None = None
        self._region: str = REGION_EU
        self._devices: list[dict[str, JsonVal]] = []
        self._client: EcoFlowApiClient | None = None

    async def async_step_user(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle the initial step - choose setup method."""
        # Show menu to choose between automatic discovery or manual entry
        return self.async_show_menu(
            step_id="user",
            menu_options=["auto_discovery", "manual_entry"],
        )

    async def async_step_auto_discovery(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle automatic device discovery via API."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                access_key = str(user_input[CONF_ACCESS_KEY])
                secret_key = str(user_input[CONF_SECRET_KEY])
                region = str(user_input.get(CONF_REGION, REGION_EU))
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=session,
                    region=region,
                )

                # Test connection and get device list
                devices = await client.get_device_list()

                self._access_key = access_key
                self._secret_key = secret_key
                self._region = region
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
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="auto_discovery",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer-eu.ecoflow.com/",
            },
        )

    async def async_step_manual_entry(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle manual entry of all device information."""
        errors: dict[str, str] = {}

        # Schema for manual entry - all fields at once
        manual_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=REGION_EU): vol.In(REGIONS),
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Required(CONF_DEVICE_SN): str,
                vol.Required(CONF_DEVICE_TYPE, default=_DEFAULT_DEVICE_TYPE): vol.In(get_device_types()),
            }
        )

        if user_input is not None:
            try:
                region = str(user_input.get(CONF_REGION, REGION_EU))
                access_key = str(user_input[CONF_ACCESS_KEY])
                secret_key = str(user_input[CONF_SECRET_KEY])
                device_sn = str(user_input[CONF_DEVICE_SN])
                device_type = str(user_input[CONF_DEVICE_TYPE])

                _LOGGER.info(
                    "Manual entry: SN=%s, Type=%s, Region=%s",
                    device_sn,
                    device_type,
                    region,
                )

                # Check if device is already configured
                await self.async_set_unique_id(device_sn)
                self._abort_if_unique_id_configured()

                # Test API credentials
                session = async_get_clientsession(self.hass)
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=session,
                    region=region,
                )

                # Try to verify device access (non-blocking)
                try:
                    quota = await client.get_device_quota(device_sn)
                    _LOGGER.info("Device verification successful: %s", quota)
                except EcoFlowApiError as err:
                    _LOGGER.warning("Device verification failed (will proceed anyway): %s", err)

                # Create entry
                device_name = get_device_types().get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: access_key,
                        CONF_SECRET_KEY: secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                        CONF_REGION: region,
                    },
                )

            except EcoFlowAuthError as err:
                _LOGGER.error("Authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except EcoFlowApiError as err:
                _LOGGER.error("API error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="manual_entry",
            data_schema=manual_schema,
            errors=errors,
            description_placeholders={
                "api_docs": "https://developer-eu.ecoflow.com/",
            },
        )

    async def async_step_select_device(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle device selection from discovered devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_sn = str(user_input[CONF_DEVICE_SN])
            device_type = str(user_input.get(CONF_DEVICE_TYPE, _DEFAULT_DEVICE_TYPE))

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
                device_name = get_device_types().get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: self._access_key,
                        CONF_SECRET_KEY: self._secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                        CONF_REGION: self._region,
                    },
                )

        # Build device options for selector
        device_options: list[SelectOptionDict] = []
        for device in self._devices:
            sn = str(device.get("sn", device.get("deviceSn", "")))
            device_name = str(device.get("deviceName", device.get("name", sn)))
            online = device.get("online", device.get("isOnline", False))
            status = "\U0001f7e2" if online else "\U0001f534"

            if sn:
                device_options.append(
                    SelectOptionDict(
                        value=sn,
                        label=f"{status} {device_name} ({sn[-4:]})",
                    )
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
                vol.Required(CONF_DEVICE_TYPE, default=_DEFAULT_DEVICE_TYPE): SelectSelector(
                    SelectSelectorConfig(
                        options=[SelectOptionDict(value=k, label=v) for k, v in get_device_types().items()],
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

    async def async_step_manual_device(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle manual device entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_sn = str(user_input[CONF_DEVICE_SN])
            device_type = str(user_input[CONF_DEVICE_TYPE])

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
                device_name = get_device_types().get(device_type, device_type)
                return self.async_create_entry(
                    title=f"EcoFlow {device_name} ({device_sn[-4:]})",
                    data={
                        CONF_ACCESS_KEY: self._access_key,
                        CONF_SECRET_KEY: self._secret_key,
                        CONF_DEVICE_SN: device_sn,
                        CONF_DEVICE_TYPE: device_type,
                    },
                )

        manual_device_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_SN): str,
                vol.Required(CONF_DEVICE_TYPE, default=_DEFAULT_DEVICE_TYPE): vol.In(get_device_types()),
            }
        )

        return self.async_show_form(
            step_id="manual_device",
            data_schema=manual_device_schema,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, JsonVal]) -> ConfigFlowResult:
        """Handle reauthorization."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                access_key = str(user_input[CONF_ACCESS_KEY])
                secret_key = str(user_input[CONF_SECRET_KEY])
                client = EcoFlowApiClient(
                    access_key=access_key,
                    secret_key=secret_key,
                    session=session,
                )

                if await client.test_connection():
                    # Update the config entry with new credentials
                    entry = self.hass.config_entries.async_get_entry(
                        self.context["entry_id"]  # type: ignore[index]
                    )
                    if entry:
                        self.hass.config_entries.async_update_entry(
                            entry,
                            data={
                                **entry.data,
                                CONF_ACCESS_KEY: access_key,
                                CONF_SECRET_KEY: secret_key,
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
    def async_get_options_flow(  # type: ignore[explicit-any]
        config_entry: config_entries.ConfigEntry,  # type: ignore[explicit-any]
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for EcoFlow API integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:  # type: ignore[explicit-any]
        """Initialize options flow."""
        super().__init__()
        self._entry = config_entry

    @property  # type: ignore[misc]
    def config_entry(self) -> config_entries.ConfigEntry:  # type: ignore[explicit-any]
        """Return config entry."""
        return self._entry

    async def async_step_init(self, user_input: dict[str, JsonVal] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)  # type: ignore[arg-type]

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
                            "description": "EcoFlow account email OR access_key (leave empty to use access_key from main config)",
                        },
                    ): str,
                    vol.Optional(
                        CONF_MQTT_PASSWORD,
                        description={
                            "suggested_value": mqtt_password,
                            "description": "EcoFlow account password OR secret_key (leave empty to use secret_key from main config)",
                        },
                    ): str,
                    vol.Optional(
                        OPTS_DIAGNOSTIC_MODE,
                        default=diagnostic_mode,
                    ): bool,
                }
            ),
        )
