"""Constants for EcoFlow API integration."""

from typing import Final

DOMAIN: Final = "ecoflow_api"

# Config
CONF_ACCESS_KEY: Final = "access_key"
CONF_SECRET_KEY: Final = "secret_key"
CONF_DEVICE_SN: Final = "device_sn"
CONF_DEVICE_TYPE: Final = "device_type"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_MQTT_ENABLED: Final = "mqtt_enabled"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"

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

# Device Options
OPTS_REFRESH_PERIOD_SEC: Final = "refresh_period_sec"
OPTS_POWER_STEP: Final = "power_step"
OPTS_DIAGNOSTIC_MODE: Final = "diagnostic_mode"
DEFAULT_REFRESH_PERIOD_SEC: Final = 15
DEFAULT_POWER_STEP: Final = 100

# Device types
DEVICE_TYPE_DELTA_PRO_3: Final = "delta_pro_3"
DEVICE_TYPE_DELTA_PRO: Final = "delta_pro"
DEVICE_TYPE_DELTA_2: Final = "delta_2"
DEVICE_TYPE_DELTA_2_MAX: Final = "delta_2_max"
DEVICE_TYPE_DELTA_MAX: Final = "delta_max"
DEVICE_TYPE_RIVER_2: Final = "river_2"
DEVICE_TYPE_RIVER_2_MAX: Final = "river_2_max"
DEVICE_TYPE_RIVER_2_PRO: Final = "river_2_pro"
DEVICE_TYPE_RIVER_3: Final = "river_3"
DEVICE_TYPE_DELTA_3_PLUS: Final = "delta_3_plus"

DEVICE_TYPES: Final = {
    DEVICE_TYPE_DELTA_PRO_3: "Delta Pro 3",
    DEVICE_TYPE_DELTA_PRO: "Delta Pro",
    DEVICE_TYPE_DELTA_3_PLUS: "Delta 3 Plus",
    DEVICE_TYPE_DELTA_2: "Delta 2",
    DEVICE_TYPE_DELTA_2_MAX: "Delta 2 Max",
    DEVICE_TYPE_DELTA_MAX: "Delta Max",
    DEVICE_TYPE_RIVER_2: "River 2",
    DEVICE_TYPE_RIVER_2_MAX: "River 2 Max",
    DEVICE_TYPE_RIVER_2_PRO: "River 2 Pro",
    DEVICE_TYPE_RIVER_3: "River 3",
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
    "slave1",
    "slave2",
    "slave3",
    "bms2",
    "bms3",
    "eb1",
    "eb2",
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
    # Device Status
    "errcode": {
        "name": "Device Error Code",
        "unit": None,
        "device_class": None,
        "icon": "mdi:alert-circle",
    },
    "devSleepState": {
        "name": "Device Sleep State",
        "unit": None,
        "device_class": None,
        "icon": "mdi:sleep",
    },
    "devStandbyTime": {
        "name": "Device Standby Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer-sleep",
    },
    "bleStandbyTime": {
        "name": "Bluetooth Standby Time",
        "unit": "h",
        "device_class": "duration",
        "icon": "mdi:bluetooth",
    },
    # Battery Status (BMS) - Additional
    "bmsChgDsgState": {
        "name": "BMS Charge/Discharge State",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-sync",
        "options": ["idle", "discharging", "charging"],
    },
    # Battery Status (CMS) - Additional
    "cmsChgDsgState": {
        "name": "CMS Charge/Discharge State",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-sync",
        "options": ["idle", "discharging", "charging"],
    },
    "cmsBmsRunState": {
        "name": "CMS BMS Run State",
        "unit": None,
        "device_class": None,
        "icon": "mdi:power",
    },
    "cmsOilSelfStart": {
        "name": "Smart Generator Auto Start",
        "unit": None,
        "device_class": None,
        "icon": "mdi:engine",
    },
    "cmsOilOffSoc": {
        "name": "Generator Auto Stop SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:engine-off",
    },
    "cmsOilOnSoc": {
        "name": "Generator Auto Start SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:engine",
    },
    # Power Flow - Additional
    "powGet5p8": {
        "name": "Power In/Out Port Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-plug",
    },
    "powGet4p81": {
        "name": "Extra Battery Port 1 Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:battery-plus",
    },
    "powGet4p82": {
        "name": "Extra Battery Port 2 Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:battery-plus",
    },
    "powGetAcLvTt30Out": {
        "name": "AC LV TT30 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    # Plug-in Info - Power Limits
    "plugInInfoAcInChgHalPowMax": {
        "name": "AC Input Half Charging Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfoPvLChgAmpMax": {
        "name": "PV Low Voltage Charging Current Max",
        "unit": "A",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "plugInInfoAcInFeq": {
        "name": "AC Input Frequency",
        "unit": "Hz",
        "device_class": "frequency",
        "icon": "mdi:sine-wave",
    },
    "plugInInfoPvLType": {
        "name": "PV Low Voltage Type",
        "unit": None,
        "device_class": None,
        "icon": "mdi:solar-power",
    },
    "plugInInfo5p8RunState": {
        "name": "Power In/Out Port Run State",
        "unit": None,
        "device_class": None,
        "icon": "mdi:power-plug",
    },
    "plugInInfo4p82RunState": {
        "name": "Extra Battery Port 2 Run State",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-plus",
    },
    "plugInInfo5p8ChgHalPowMax": {
        "name": "Power In/Out Port Half Charging Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfoPvHChgAmpMax": {
        "name": "PV High Voltage Charging Current Max",
        "unit": "A",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "plugInInfo5p8DsgPowMax": {
        "name": "Power In/Out Port Discharge Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-plug",
    },
    "plugInInfoAcInChgPowMax": {
        "name": "AC Input Charging Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfoPvHType": {
        "name": "PV High Voltage Type",
        "unit": None,
        "device_class": None,
        "icon": "mdi:solar-power",
    },
    "plugInInfoAcOutDsgPowMax": {
        "name": "AC Output Discharge Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "plugInInfo5p8ChgPowMax": {
        "name": "Power In/Out Port Charging Power Max",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfoPvHDcAmpMax": {
        "name": "PV High Voltage DC Current Max",
        "unit": "A",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "plugInInfoPvLChgVolMax": {
        "name": "PV Low Voltage Charging Voltage Max",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfoPvLDcAmpMax": {
        "name": "PV Low Voltage DC Current Max",
        "unit": "A",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "plugInInfoPvHChgVolMax": {
        "name": "PV High Voltage Charging Voltage Max",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:lightning-bolt",
    },
    "plugInInfo4p81Sn": {
        "name": "Extra Battery Port 1 Serial Number",
        "unit": None,
        "device_class": None,
        "icon": "mdi:barcode",
    },
    "plugInInfo5p8Sn": {
        "name": "Power In/Out Port Serial Number",
        "unit": None,
        "device_class": None,
        "icon": "mdi:barcode",
    },
    "plugInInfo4p82Sn": {
        "name": "Extra Battery Port 2 Serial Number",
        "unit": None,
        "device_class": None,
        "icon": "mdi:barcode",
    },
    "plugInInfo4p81RunState": {
        "name": "Extra Battery Port 1 Run State",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-plus",
    },
    "plugInInfo4p81DsgChgType": {
        "name": "Extra Battery Port 1 Charge/Discharge Type",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-sync",
    },
    "plugInInfo4p82DsgChgType": {
        "name": "Extra Battery Port 2 Charge/Discharge Type",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-sync",
    },
    "plugInInfo5p8DsgChg": {
        "name": "Power In/Out Port Charge/Discharge",
        "unit": None,
        "device_class": None,
        "icon": "mdi:battery-sync",
    },
    # Flow Info - Additional (these are already in binary sensors, but adding as sensors too)
    "flowInfoPvL": {
        "name": "PV Low Voltage Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:solar-power",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoPvH": {
        "name": "PV High Voltage Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:solar-power",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoTypec1": {
        "name": "Type-C 1 Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:usb-c-port",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoTypec2": {
        "name": "Type-C 2 Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:usb-c-port",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoAcLvOut": {
        "name": "AC LV Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:power-socket",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo4p82Out": {
        "name": "Extra Battery Port 2 Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-plus",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoAcIn": {
        "name": "AC Input Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:power-plug",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoAcHvOut": {
        "name": "AC HV Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:power-socket",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo12v": {
        "name": "12V Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:current-dc",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo24v": {
        "name": "24V Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:current-dc",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo4p81In": {
        "name": "Extra Battery Port 1 Input Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-plus",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoQcusb1": {
        "name": "QC USB 1 Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:usb-port",
        "options": ["off", "unknown", "on"],
    },
    "flowInfoQcusb2": {
        "name": "QC USB 2 Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:usb-port",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo4p82In": {
        "name": "Extra Battery Port 2 Input Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-plus",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo5p8In": {
        "name": "Power In/Out Port Input Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:power-plug",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo4p81Out": {
        "name": "Extra Battery Port 1 Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:battery-plus",
        "options": ["off", "unknown", "on"],
    },
    "flowInfo5p8Out": {
        "name": "Power In/Out Port Output Flow Status",
        "unit": None,
        "device_class": "enum",
        "icon": "mdi:power-plug",
        "options": ["off", "unknown", "on"],
    },
    # Additional Settings
    "fastChargeSwitch": {
        "name": "Fast Charge Switch",
        "unit": None,
        "device_class": None,
        "icon": "mdi:lightning-bolt",
    },
    "energyBackupEn": {
        "name": "Energy Backup Enabled",
        "unit": None,
        "device_class": None,
        "icon": "mdi:backup-restore",
    },
    "llcHvLvFlag": {
        "name": "HV/LV AC Flag",
        "unit": None,
        "device_class": None,
        "icon": "mdi:power-plug",
    },
    "acLvAlwaysOn": {
        "name": "AC LV Always On",
        "unit": None,
        "device_class": None,
        "icon": "mdi:power-socket",
    },
    "energyBackupStartSoc": {
        "name": "Energy Backup Start SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:backup-restore",
    },
    "acHvAlwaysOn": {
        "name": "AC HV Always On",
        "unit": None,
        "device_class": None,
        "icon": "mdi:power-socket",
    },
    "acAlwaysOnMiniSoc": {
        "name": "AC Always On Minimum SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:power-socket",
    },
    "generatorPvHybridModeOpen": {
        "name": "Generator PV Hybrid Mode",
        "unit": None,
        "device_class": None,
        "icon": "mdi:engine",
    },
    "generatorCareModeOpen": {
        "name": "Generator Care Mode",
        "unit": None,
        "device_class": None,
        "icon": "mdi:engine",
    },
    "generatorPvHybridModeSocMax": {
        "name": "Generator PV Hybrid Mode Max SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:engine",
    },
    # MQTT-only sensors (available only when MQTT is enabled)
    "bmsCycles": {
        "name": "Battery Cycles",
        "key": "cycles",  # MQTT field name
        "unit": "cycles",
        "device_class": None,
        "icon": "mdi:sync",
        "mqtt_only": True,  # Only available via MQTT
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

# ============================================================================
# DELTA PRO (Original) - API Definitions
# Based on EcoFlow Developer API documentation
# ============================================================================

# Delta Pro Sensors - based on GetAllQuotaResponse
DELTA_PRO_SENSORS: Final = {
    # ============================================================================
    # BMS Master - Battery Management System
    # ============================================================================
    "bmsMaster.soc": {
        "name": "Battery Level",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "bmsMaster.temp": {
        "name": "Battery Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "bmsMaster.inputWatts": {
        "name": "Battery Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:battery-charging",
    },
    "bmsMaster.outputWatts": {
        "name": "Battery Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:battery-arrow-down",
    },
    "bmsMaster.vol": {
        "name": "Battery Voltage",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "bmsMaster.amp": {
        "name": "Battery Current",
        "unit": "A",
        "device_class": "current",
        "icon": "mdi:current-dc",
    },
    "bmsMaster.soh": {
        "name": "Battery Health",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:battery-heart",
    },
    "bmsMaster.designCap": {
        "name": "Design Capacity",
        "unit": "mAh",
        "device_class": None,
        "icon": "mdi:battery-high",
    },
    "bmsMaster.remainCap": {
        "name": "Remaining Capacity",
        "unit": "mAh",
        "device_class": None,
        "icon": "mdi:battery",
    },
    "bmsMaster.fullCap": {
        "name": "Full Capacity",
        "unit": "mAh",
        "device_class": None,
        "icon": "mdi:battery-high",
    },
    "bmsMaster.maxCellVol": {
        "name": "Max Cell Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "bmsMaster.minCellVol": {
        "name": "Min Cell Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "bmsMaster.maxCellTemp": {
        "name": "Max Cell Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-high",
    },
    "bmsMaster.minCellTemp": {
        "name": "Min Cell Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-low",
    },
    "bmsMaster.maxMosTemp": {
        "name": "Max MOS Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-high",
    },
    "bmsMaster.minMosTemp": {
        "name": "Min MOS Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer-low",
    },
    "bmsMaster.remainTime": {
        "name": "Battery Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer",
    },
    "bmsMaster.errCode": {
        "name": "BMS Error Code",
        "unit": None,
        "device_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # Inverter
    # ============================================================================
    "inv.inputWatts": {
        "name": "Inverter Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-plug",
    },
    "inv.outputWatts": {
        "name": "Inverter Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "inv.invOutVol": {
        "name": "AC Output Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "inv.invOutAmp": {
        "name": "AC Output Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "inv.invOutFreq": {
        "name": "AC Output Frequency",
        "unit": "Hz",
        "device_class": "frequency",
        "icon": "mdi:sine-wave",
    },
    "inv.acInVol": {
        "name": "AC Input Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "inv.acInAmp": {
        "name": "AC Input Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:current-ac",
    },
    "inv.acInFreq": {
        "name": "AC Input Frequency",
        "unit": "Hz",
        "device_class": "frequency",
        "icon": "mdi:sine-wave",
    },
    "inv.outTemp": {
        "name": "Inverter Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "inv.dcInVol": {
        "name": "DC Input Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "inv.dcInAmp": {
        "name": "DC Input Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:current-dc",
    },
    "inv.dcInTemp": {
        "name": "DC Input Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "inv.cfgAcOutFreq": {
        "name": "Configured AC Output Frequency",
        "unit": None,
        "device_class": None,
        "icon": "mdi:sine-wave",
    },
    "inv.cfgSlowChgWatts": {
        "name": "AC Slow Charging Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "inv.cfgFastChgWatts": {
        "name": "AC Fast Charging Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:lightning-bolt",
    },
    "inv.cfgStandbyMin": {
        "name": "AC Standby Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer",
    },
    "inv.errCode": {
        "name": "Inverter Error Code",
        "unit": None,
        "device_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # MPPT - Solar Charger
    # ============================================================================
    "mppt.inVol": {
        "name": "Solar Input Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:solar-power",
    },
    "mppt.inAmp": {
        "name": "Solar Input Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:solar-power",
    },
    "mppt.inWatts": {
        "name": "Solar Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:solar-power",
    },
    "mppt.outVol": {
        "name": "MPPT Output Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:flash",
    },
    "mppt.outAmp": {
        "name": "MPPT Output Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:current-dc",
    },
    "mppt.outWatts": {
        "name": "MPPT Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:flash",
    },
    "mppt.mpptTemp": {
        "name": "MPPT Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "mppt.dcdc12vVol": {
        "name": "DC 12V Output Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:car-battery",
    },
    "mppt.dcdc12vAmp": {
        "name": "DC 12V Output Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:car-battery",
    },
    "mppt.dcdc12vWatts": {
        "name": "DC 12V Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:car-battery",
    },
    "mppt.carOutVol": {
        "name": "Car Charger Output Voltage",
        "unit": "mV",
        "device_class": "voltage",
        "icon": "mdi:car",
    },
    "mppt.carOutAmp": {
        "name": "Car Charger Output Current",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:car",
    },
    "mppt.carOutWatts": {
        "name": "Car Charger Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:car",
    },
    "mppt.carTemp": {
        "name": "Car Charger Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "mppt.cfgDcChgCurrent": {
        "name": "Car Charging Current Setting",
        "unit": "mA",
        "device_class": "current",
        "icon": "mdi:car-battery",
    },
    "mppt.faultCode": {
        "name": "MPPT Fault Code",
        "unit": None,
        "device_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # PD - Power Distribution
    # ============================================================================
    "pd.soc": {
        "name": "Display SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "pd.wattsOutSum": {
        "name": "Total Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-export",
    },
    "pd.wattsInSum": {
        "name": "Total Input Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:transmission-tower-import",
    },
    "pd.remainTime": {
        "name": "Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer",
    },
    "pd.usb1Watts": {
        "name": "USB 1 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "pd.usb2Watts": {
        "name": "USB 2 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "pd.qcUsb1Watts": {
        "name": "QC USB 1 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "pd.qcUsb2Watts": {
        "name": "QC USB 2 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-port",
    },
    "pd.typec1Watts": {
        "name": "Type-C 1 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-c-port",
    },
    "pd.typec2Watts": {
        "name": "Type-C 2 Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:usb-c-port",
    },
    "pd.typec1Temp": {
        "name": "Type-C 1 Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "pd.typec2Temp": {
        "name": "Type-C 2 Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "pd.carWatts": {
        "name": "Car Output Power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:car",
    },
    "pd.carTemp": {
        "name": "Car Output Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "pd.standByMode": {
        "name": "Device Standby Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:timer-sleep",
    },
    "pd.lcdOffSec": {
        "name": "Screen Off Time",
        "unit": "s",
        "device_class": "duration",
        "icon": "mdi:monitor-off",
    },
    "pd.lcdBrightness": {
        "name": "Screen Brightness",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:brightness-6",
    },
    "pd.chgPowerDc": {
        "name": "Cumulative DC Charged",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:battery-charging",
    },
    "pd.chgSunPower": {
        "name": "Cumulative Solar Charged",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:solar-power",
    },
    "pd.chgPowerAc": {
        "name": "Cumulative AC Charged",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:power-plug",
    },
    "pd.dsgPowerDc": {
        "name": "Cumulative DC Discharged",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:battery-arrow-down",
    },
    "pd.dsgPowerAc": {
        "name": "Cumulative AC Discharged",
        "unit": "Wh",
        "device_class": "energy",
        "icon": "mdi:power-socket",
    },
    "pd.errCode": {
        "name": "PD Error Code",
        "unit": None,
        "device_class": None,
        "icon": "mdi:alert-circle",
    },
    "pd.wifiRssi": {
        "name": "WiFi Signal Strength",
        "unit": "dBm",
        "device_class": "signal_strength",
        "icon": "mdi:wifi",
    },
    # ============================================================================
    # EMS - Energy Management System
    # ============================================================================
    "ems.maxChargeSoc": {
        "name": "Max Charge Level",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:battery-charging-100",
    },
    "ems.minDsgSoc": {
        "name": "Min Discharge Level",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:battery-10",
    },
    "ems.minOpenOilEbSoc": {
        "name": "Generator Auto Start SOC",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:engine",
    },
    "ems.maxCloseOilEbSoc": {
        "name": "Generator Auto Stop SOC",
        "unit": "%",
        "device_class": None,
        "icon": "mdi:engine-off",
    },
    "ems.chgRemainTime": {
        "name": "Charge Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-charging",
    },
    "ems.dsgRemainTime": {
        "name": "Discharge Remaining Time",
        "unit": "min",
        "device_class": "duration",
        "icon": "mdi:battery-arrow-down",
    },
    "ems.lcdShowSoc": {
        "name": "LCD Display SOC",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
    "ems.f32LcdShowSoc": {
        "name": "LCD Display SOC (Float)",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
    },
}

# Delta Pro Binary Sensors
DELTA_PRO_BINARY_SENSORS: Final = {
    "inv.cfgAcEnabled": {
        "name": "AC Output Enabled",
        "device_class": "power",
        "icon": "mdi:power-socket",
    },
    "inv.cfgAcXboost": {
        "name": "X-Boost Enabled",
        "device_class": None,
        "icon": "mdi:lightning-bolt",
    },
    "mppt.carState": {
        "name": "Car Charger Enabled",
        "device_class": None,
        "icon": "mdi:car",
    },
    "pd.beepState": {
        "name": "Beep Enabled",
        "device_class": None,
        "icon": "mdi:volume-high",
    },
    "pd.dcOutState": {
        "name": "DC Output Enabled",
        "device_class": "power",
        "icon": "mdi:current-dc",
    },
    "pd.carState": {
        "name": "Car Output Enabled",
        "device_class": None,
        "icon": "mdi:car",
    },
    "inv.acPassbyAutoEn": {
        "name": "Bypass AC Auto Start",
        "device_class": None,
        "icon": "mdi:power-plug",
    },
}

# Delta Pro Switches - controllable settings
DELTA_PRO_SWITCHES: Final = {
    "ac_output": {
        "name": "AC Output",
        "state_key": "inv.cfgAcEnabled",
        "cmd_set": 32,
        "cmd_id": 66,
        "param_key": "enabled",
        "icon_on": "mdi:power-socket",
        "icon_off": "mdi:power-socket-off",
    },
    "x_boost": {
        "name": "X-Boost",
        "state_key": "inv.cfgAcXboost",
        "cmd_set": 32,
        "cmd_id": 66,
        "param_key": "xboost",
        "icon_on": "mdi:lightning-bolt",
        "icon_off": "mdi:lightning-bolt-outline",
    },
    "car_charger": {
        "name": "Car Charger",
        "state_key": "mppt.carState",
        "cmd_set": 32,
        "cmd_id": 81,
        "param_key": "enabled",
        "icon_on": "mdi:car",
        "icon_off": "mdi:car-off",
    },
    "beeper": {
        "name": "Beeper",
        "state_key": "pd.beepState",
        "cmd_set": 32,
        "cmd_id": 38,
        "param_key": "enabled",
        "icon_on": "mdi:volume-high",
        "icon_off": "mdi:volume-off",
    },
    "bypass_ac_auto_start": {
        "name": "Bypass AC Auto Start",
        "state_key": "inv.acPassbyAutoEn",
        "cmd_set": 32,
        "cmd_id": 84,
        "param_key": "enabled",
        "icon_on": "mdi:power-plug",
        "icon_off": "mdi:power-plug-off",
    },
}

# Delta Pro Numbers - adjustable values
DELTA_PRO_NUMBERS: Final = {
    "max_charge_level": {
        "name": "Max Charge Level",
        "state_key": "ems.maxChargeSoc",
        "cmd_set": 32,
        "cmd_id": 49,
        "param_key": "maxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": "%",
        "icon": "mdi:battery-charging-100",
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "state_key": "ems.minDsgSoc",
        "cmd_set": 32,
        "cmd_id": 51,
        "param_key": "minDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": "%",
        "icon": "mdi:battery-10",
    },
    "car_input_current": {
        "name": "Car Input Current",
        "state_key": "mppt.cfgDcChgCurrent",
        "cmd_set": 32,
        "cmd_id": 71,
        "param_key": "currMa",
        "min": 4000,
        "max": 8000,
        "step": 1000,
        "unit": "mA",
        "icon": "mdi:car-battery",
    },
    "screen_brightness": {
        "name": "Screen Brightness",
        "state_key": "pd.lcdBrightness",
        "cmd_set": 32,
        "cmd_id": 39,
        "param_key": "lcdBrightness",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit": "%",
        "icon": "mdi:brightness-6",
    },
    "device_standby_time": {
        "name": "Device Standby Time",
        "state_key": "pd.standByMode",
        "cmd_set": 32,
        "cmd_id": 33,
        "param_key": "standByMode",
        "min": 0,
        "max": 5999,
        "step": 30,
        "unit": "min",
        "icon": "mdi:timer-sleep",
    },
    "screen_timeout": {
        "name": "Screen Timeout",
        "state_key": "pd.lcdOffSec",
        "cmd_set": 32,
        "cmd_id": 39,
        "param_key": "lcdTime",
        "min": 0,
        "max": 1800,
        "step": 30,
        "unit": "s",
        "icon": "mdi:monitor-off",
    },
    "ac_standby_time": {
        "name": "AC Standby Time",
        "state_key": "inv.cfgStandbyMin",
        "cmd_set": 32,
        "cmd_id": 153,
        "param_key": "standByMins",
        "min": 0,
        "max": 720,
        "step": 30,
        "unit": "min",
        "icon": "mdi:timer",
    },
    "ac_charging_power": {
        "name": "AC Charging Power",
        "state_key": "inv.cfgSlowChgWatts",
        "cmd_set": 32,
        "cmd_id": 69,
        "param_key": "slowChgPower",
        "min": 200,
        "max": 2900,
        "step": 100,
        "unit": "W",
        "icon": "mdi:lightning-bolt",
    },
    "generator_auto_start_soc": {
        "name": "Generator Auto Start SOC",
        "state_key": "ems.minOpenOilEbSoc",
        "cmd_set": 32,
        "cmd_id": 52,
        "param_key": "openOilSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": "%",
        "icon": "mdi:engine",
    },
    "generator_auto_stop_soc": {
        "name": "Generator Auto Stop SOC",
        "state_key": "ems.maxCloseOilEbSoc",
        "cmd_set": 32,
        "cmd_id": 53,
        "param_key": "closeOilSoc",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit": "%",
        "icon": "mdi:engine-off",
    },
}

# Delta Pro Selects - dropdown options
DELTA_PRO_SELECTS: Final = {
    "pv_charging_type": {
        "name": "PV Charging Type",
        "state_key": "mppt.cfgChgType",
        "cmd_set": 32,
        "cmd_id": 82,
        "param_key": "chgType",
        "icon": "mdi:solar-power",
        "options": {
            "Auto": 0,
            "MPPT": 1,
            "Adapter": 2,
        },
    },
    "ac_output_frequency": {
        "name": "AC Output Frequency",
        "state_key": "inv.cfgAcOutFreq",
        "cmd_set": 32,
        "cmd_id": 66,
        "param_key": "cfgAcOutFreq",
        "icon": "mdi:sine-wave",
        "options": {
            "50 Hz": 1,
            "60 Hz": 2,
        },
    },
}
