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
# Based on real API response from Delta Pro 3 device
DELTA_PRO_3_SENSORS: Final = {
    # Battery Status (BMS)
    "bmsBattSoc": {
        "name": "Battery Level (BMS)",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "bmsBattSoh": {
        "name": "State of Health (BMS)",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery-heart",
    },
    "bmsChgRemTime": {
        "name": "Charge Remaining Time (BMS)",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-charging",
    },
    "bmsDsgRemTime": {
        "name": "Discharge Remaining Time (BMS)",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-arrow-down",
    },
    "bmsDesignCap": {
        "name": "Design Capacity",
        "unit": "mAh",
        "device_class": None,
        "icon": "mdi:battery-high",
    },
    # Battery Status (CMS)
    "cmsBattSoc": {
        "name": "Battery Level (CMS)",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "cmsBattSoh": {
        "name": "State of Health (CMS)",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery-heart",
    },
    # Note: Cycles are not available via REST API for Delta Pro 3
    # They are only available via MQTT (WebSocket) connection
    # We can estimate cycles based on SOH: estimated_cycles ≈ (100 - SOH) × 10
    # For a new battery (SOH=100%), estimated cycles ≈ 0
    # For a degraded battery (SOH=80%), estimated cycles ≈ 200
    "cmsChgRemTime": {
        "name": "Charge Remaining Time (CMS)",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-charging",
    },
    "cmsDsgRemTime": {
        "name": "Discharge Remaining Time (CMS)",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-arrow-down",
    },
    "cmsBattFullEnergy": {
        "name": "Full Energy Capacity",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:battery-high",
    },
    "cmsMaxChgSoc": {
        "name": "Max Charge Level",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery-charging-100",
    },
    "cmsMinDsgSoc": {
        "name": "Min Discharge Level",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery-low",
    },
    # Power Flow
    "powInSumW": {
        "name": "Total Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-import",
    },
    "powOutSumW": {
        "name": "Total Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-export",
    },
    "powGetAcIn": {
        "name": "AC Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-plug",
    },
    "powGetAc": {
        "name": "AC Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "powGetAcHvOut": {
        "name": "AC HV Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "powGetAcLvOut": {
        "name": "AC LV Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "powGetPvH": {
        "name": "Solar Input Power (High)",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:solar-power",
    },
    "powGetPvL": {
        "name": "Solar Input Power (Low)",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:solar-power",
    },
    "powGet12v": {
        "name": "12V DC Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:current-dc",
    },
    "powGet24v": {
        "name": "24V DC Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:current-dc",
    },
    "powGetTypec1": {
        "name": "USB-C1 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "powGetTypec2": {
        "name": "USB-C2 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "powGetQcusb1": {
        "name": "QC USB1 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "powGetQcusb2": {
        "name": "QC USB2 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    # Temperature Sensors
    "bmsMaxCellTemp": {
        "name": "Max Cell Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-high",
    },
    "bmsMinCellTemp": {
        "name": "Min Cell Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-low",
    },
    "bmsMaxMosTemp": {
        "name": "Max MOSFET Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-high",
    },
    "bmsMinMosTemp": {
        "name": "Min MOSFET Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-low",
    },
    # Settings
    "acStandbyTime": {
        "name": "AC Standby Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer-outline",
    },
    "dcStandbyTime": {
        "name": "DC Standby Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer-outline",
    },
    "screenOffTime": {
        "name": "Screen Off Time",
        "unit": "s",
        "device_class": "duration",
        "icon": "mdi:monitor-off",
    },
    "lcdLight": {
        "name": "LCD Brightness",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:brightness-6",
    },
    # AC Output
    "acOutFreq": {
        "name": "AC Output Frequency",
        "unit": "Hz",
        "device_class": "frequency",
        "icon": "mdi:sine-wave",
    },
}

# Binary Sensors for Delta Pro 3 (status indicators)
DELTA_PRO_3_BINARY_SENSORS: Final = {
    "plugInInfoAcChargerFlag": {
        "name": "AC Charging",
        "device_class": "battery_charging",
        "icon": "mdi:power-plug",
    },
    "plugInInfoPvHChargerFlag": {
        "name": "Solar Charging (High)",
        "device_class": "battery_charging",
        "icon": "mdi:solar-power",
    },
    "plugInInfoPvLChargerFlag": {
        "name": "Solar Charging (Low)",
        "device_class": "battery_charging",
        "icon": "mdi:solar-power",
    },
    "plugInInfo4p81ChargerFlag": {
        "name": "4P81 Charging",
        "device_class": "battery_charging",
        "icon": "mdi:battery-charging",
    },
    "plugInInfo4p82ChargerFlag": {
        "name": "4P82 Charging",
        "device_class": "battery_charging",
        "icon": "mdi:battery-charging",
    },
    "plugInInfo5p8ChargerFlag": {
        "name": "5P8 Charging",
        "device_class": "battery_charging",
        "icon": "mdi:battery-charging",
    },
    "xboostEn": {
        "name": "X-Boost Enabled",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "enBeep": {
        "name": "Beep Enabled",
        "device_class": None,
        "icon": "mdi:volume-high",
    },
    "acEnergySavingOpen": {
        "name": "AC Energy Saving",
        "device_class": None,
        "icon": "mdi:leaf",
    },
    "energyBackupEn": {
        "name": "Energy Backup Enabled",
        "device_class": None,
        "icon": "mdi:backup-restore",
    },
    "stormPatternEnable": {
        "name": "Storm Pattern Enabled",
        "device_class": None,
        "icon": "mdi:weather-lightning",
    },
    "generatorCareModeOpen": {
        "name": "Generator Care Mode",
        "device_class": None,
        "icon": "mdi:engine",
    },
    "llcGFCIFlag": {
        "name": "GFCI Triggered",
        "device_class": "problem",
        "icon": "mdi:alert-circle",
    },
}

# Switches for Delta Pro 3 (controllable settings)
DELTA_PRO_3_SWITCHES: Final = {
    "xboostEn": {
        "name": "X-Boost",
        "icon": "mdi:lightning-bolt",
        "command": "WN511_SET_X_BOOST",
        "param_key": "xBoostState",
    },
    "enBeep": {
        "name": "Beep",
        "icon": "mdi:volume-high",
        "command": "WN511_SET_BEEP",
        "param_key": "beepState",
    },
    "acEnergySavingOpen": {
        "name": "AC Energy Saving",
        "icon": "mdi:leaf",
        "command": "WN511_SET_AC_OUT",  # May need specific command
        "param_key": "acOutState",
    },
}

# Number entities for Delta Pro 3 (adjustable values)
DELTA_PRO_3_NUMBERS: Final = {
    "plugInInfoAcInChgPowMax": {
        "name": "AC Charging Power",
        "unit": "W",
        "min": 200,
        "max": 3000,
        "step": 100,
        "icon": "mdi:lightning-bolt",
        "command": "WN511_SET_AC_CHARGE_SPEED",
        "param_key": "acChgPower",
    },
    "cmsMaxChgSoc": {
        "name": "Max Charge Level",
        "unit": "%",
        "min": 50,
        "max": 100,
        "step": 1,
        "icon": "mdi:battery-charging-100",
        "command": "WN511_SET_CHARGE_LEVEL",
        "param_key": "maxChgSoc",
    },
    "cmsMinDsgSoc": {
        "name": "Min Discharge Level",
        "unit": "%",
        "min": 0,
        "max": 30,
        "step": 1,
        "icon": "mdi:battery-low",
        "command": "WN511_SET_CHARGE_LEVEL",
        "param_key": "minDsgSoc",
    },
    "acStandbyTime": {
        "name": "AC Standby Time",
        "unit": "min",
        "min": 0,
        "max": 1440,
        "step": 1,
        "icon": "mdi:timer-outline",
        "command": "WN511_SET_AC_STANDBY_TIME",
        "param_key": "acStandbyTime",
    },
    "dcStandbyTime": {
        "name": "DC Standby Time",
        "unit": "min",
        "min": 0,
        "max": 1440,
        "step": 1,
        "icon": "mdi:timer-outline",
        "command": "WN511_SET_DC_STANDBY_TIME",
        "param_key": "dcStandbyTime",
    },
    "screenOffTime": {
        "name": "Screen Off Time",
        "unit": "s",
        "min": 0,
        "max": 3600,
        "step": 10,
        "icon": "mdi:monitor-off",
        "command": "WN511_SET_LCD_STANDBY_TIME",
        "param_key": "lcdOffTime",
    },
    "lcdLight": {
        "name": "LCD Brightness",
        "unit": "%",
        "min": 0,
        "max": 100,
        "step": 1,
        "icon": "mdi:brightness-6",
        "command": "WN511_SET_LCD_BRIGHTNESS",  # May need verification
        "param_key": "lcdLight",
    },
}


