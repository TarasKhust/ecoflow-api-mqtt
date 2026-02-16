"""Constants for EcoFlow API integration."""

from typing import Final

DOMAIN: Final = "ecoflow_api"

# Config
CONF_ACCESS_KEY: Final = "access_key"
CONF_SECRET_KEY: Final = "secret_key"  # noqa: S105
CONF_DEVICE_SN: Final = "device_sn"
CONF_DEVICE_TYPE: Final = "device_type"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_MQTT_ENABLED: Final = "mqtt_enabled"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"  # noqa: S105
CONF_REGION: Final = "region"

# API Regions
REGION_EU: Final = "eu"
REGION_US: Final = "us"

API_BASE_URL_EU: Final = "https://api-e.ecoflow.com"
API_BASE_URL_US: Final = "https://api.ecoflow.com"

# Default to EU for backward compatibility
API_BASE_URL: Final = API_BASE_URL_EU
API_TIMEOUT: Final = 30

REGIONS: Final = {
    REGION_EU: "Europe (api-e.ecoflow.com)",
    REGION_US: "United States (api.ecoflow.com)",
}

# Update interval
DEFAULT_UPDATE_INTERVAL: Final = 15  # seconds
UPDATE_INTERVAL_OPTIONS: Final = {
    "5": 5,
    "10": 10,
    "15": 15,
    "30": 30,
    "60": 60,
}

# Device Options
OPTS_REFRESH_PERIOD_SEC: Final = "refresh_period_sec"
OPTS_POWER_STEP: Final = "power_step"
OPTS_DIAGNOSTIC_MODE: Final = "diagnostic_mode"
DEFAULT_REFRESH_PERIOD_SEC: Final = 15
DEFAULT_POWER_STEP: Final = 100
