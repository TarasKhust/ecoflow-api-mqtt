"""Constants for EcoFlow API integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "ecoflow_api"

# Config
CONF_ACCESS_KEY: Final = "access_key"
CONF_SECRET_KEY: Final = "secret_key"
CONF_DEVICE_SN: Final = "device_sn"
CONF_DEVICE_TYPE: Final = "device_type"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# API
API_BASE_URL: Final = "https://api-e.ecoflow.com"
API_TIMEOUT: Final = 30

# Update interval
DEFAULT_UPDATE_INTERVAL: Final = 15  # seconds
UPDATE_INTERVAL_OPTIONS: Final = {
    "5": 5,
    "10": 10,
    "15": 15,
    "30": 30,
    "60": 60,
}

# Device types
DEVICE_TYPE_DELTA_PRO_3: Final = "delta_pro_3"
DEVICE_TYPE_DELTA_PRO: Final = "delta_pro"
DEVICE_TYPE_DELTA_2: Final = "delta_2"
DEVICE_TYPE_DELTA_2_MAX: Final = "delta_2_max"
DEVICE_TYPE_DELTA_MAX: Final = "delta_max"
DEVICE_TYPE_RIVER_2: Final = "river_2"
DEVICE_TYPE_RIVER_2_MAX: Final = "river_2_max"
DEVICE_TYPE_RIVER_2_PRO: Final = "river_2_pro"

DEVICE_TYPES: Final = {
    DEVICE_TYPE_DELTA_PRO_3: "Delta Pro 3",
    DEVICE_TYPE_DELTA_PRO: "Delta Pro",
    DEVICE_TYPE_DELTA_2: "Delta 2",
    DEVICE_TYPE_DELTA_2_MAX: "Delta 2 Max",
    DEVICE_TYPE_DELTA_MAX: "Delta Max",
    DEVICE_TYPE_RIVER_2: "River 2",
    DEVICE_TYPE_RIVER_2_MAX: "River 2 Max",
    DEVICE_TYPE_RIVER_2_PRO: "River 2 Pro",
}

# Delta Pro 3 Commands (from https://developer-eu.ecoflow.com/us/document/deltaPro3)
CMD_DELTA_PRO_3_SET_AC_CHARGE_SPEED: Final = "WN511_SET_AC_CHARGE_SPEED"
CMD_DELTA_PRO_3_SET_CHARGE_LEVEL: Final = "WN511_SET_CHARGE_LEVEL"
CMD_DELTA_PRO_3_SET_AC_OUT: Final = "WN511_SET_AC_OUT"
CMD_DELTA_PRO_3_SET_DC_OUT: Final = "WN511_SET_DC_OUT"
CMD_DELTA_PRO_3_SET_12V_DC_OUT: Final = "WN511_SET_12V_DC_OUT"
CMD_DELTA_PRO_3_SET_24V_DC_OUT: Final = "WN511_SET_24V_DC_OUT"
CMD_DELTA_PRO_3_SET_USB_OUT: Final = "WN511_SET_USB_OUT"
CMD_DELTA_PRO_3_SET_AC_STANDBY_TIME: Final = "WN511_SET_AC_STANDBY_TIME"
CMD_DELTA_PRO_3_SET_DC_STANDBY_TIME: Final = "WN511_SET_DC_STANDBY_TIME"
CMD_DELTA_PRO_3_SET_LCD_STANDBY_TIME: Final = "WN511_SET_LCD_STANDBY_TIME"
CMD_DELTA_PRO_3_SET_BEEP: Final = "WN511_SET_BEEP"
CMD_DELTA_PRO_3_SET_X_BOOST: Final = "WN511_SET_X_BOOST"

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor", "switch", "number", "select"]

# Extra Battery prefixes that can be detected in API response
EXTRA_BATTERY_PREFIXES: Final = [
    "slave1", "slave2", "slave3",
    "bms2", "bms3",
    "eb1", "eb2",
    "extraBms",
    "slaveBattery",
]

# Sensor keys mapping for Delta Pro 3
DELTA_PRO_3_SENSORS: Final = {
    "soc": {
        "name": "Battery Level",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "wattsInSum": {
        "name": "Total In Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-import",
    },
    "wattsOutSum": {
        "name": "Total Out Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-export",
    },
    "bmsTemp": {
        "name": "Battery Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "chgRemainTime": {
        "name": "Charge Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-charging",
    },
    "dsgRemainTime": {
        "name": "Discharge Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-arrow-down",
    },
    "acInPower": {
        "name": "AC In Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-plug",
    },
    "acOutPower": {
        "name": "AC Out Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "dcOutPower": {
        "name": "DC Out Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:current-dc",
    },
    "solarInPower": {
        "name": "Solar In Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:solar-power",
    },
    "cycles": {
        "name": "Cycles",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-heart-variant",
    },
    "soh": {
        "name": "State of Health",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery-heart",
    },
}


