"""Sensor platform for EcoFlow API integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfFrequency,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity
from .hybrid_coordinator import EcoFlowHybridCoordinator

_LOGGER = logging.getLogger(__name__)


# Sensor definitions for Delta Pro 3 based on real API keys
DELTA_PRO_3_SENSOR_DEFINITIONS = {
    # ============================================================================
    # BATTERY - Main Battery (BMS)
    # ============================================================================
    "bms_batt_soc": {
        "name": "Battery Level",
        "key": "bmsBattSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_batt_soh": {
        "name": "Battery Health",
        "key": "bmsBattSoh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "bms_design_cap": {
        "name": "Battery Design Capacity",
        "key": "bmsDesignCap",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "bms_chg_rem_time": {
        "name": "Charge Remaining Time",
        "key": "bmsChgRemTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "bms_dsg_rem_time": {
        "name": "Discharge Remaining Time",
        "key": "bmsDsgRemTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "bms_chg_dsg_state": {
        "name": "Charge/Discharge State",
        "key": "bmsChgDsgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-sync",
        "options": ["idle", "charging", "discharging"],
    },
    "bms_err_code": {
        "name": "BMS Error Code",
        "key": "bmsErrCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    
    # ============================================================================
    # BATTERY - CMS (Combined Management System)
    # ============================================================================
    "cms_batt_soc": {
        "name": "System Battery Level",
        "key": "cmsBattSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "cms_batt_soh": {
        "name": "System Battery Health",
        "key": "cmsBattSoh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "cms_batt_full_energy": {
        "name": "System Full Energy",
        "key": "cmsBattFullEnergy",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "cms_batt_pow_in_max": {
        "name": "Max Input Power",
        "key": "cmsBattPowInMax",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-high",
    },
    "cms_batt_pow_out_max": {
        "name": "Max Output Power",
        "key": "cmsBattPowOutMax",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "cms_bms_run_state": {
        "name": "BMS Run State",
        "key": "cmsBmsRunState",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:state-machine",
    },
    "cms_chg_dsg_state": {
        "name": "System Charge/Discharge State",
        "key": "cmsChgDsgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-sync",
        "options": ["idle", "charging", "discharging"],
    },
    "cms_chg_rem_time": {
        "name": "System Charge Remaining Time",
        "key": "cmsChgRemTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "cms_dsg_rem_time": {
        "name": "System Discharge Remaining Time",
        "key": "cmsDsgRemTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "cms_max_chg_soc": {
        "name": "Max Charge Level Setting",
        "key": "cmsMaxChgSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    "cms_min_dsg_soc": {
        "name": "Min Discharge Level Setting",
        "key": "cmsMinDsgSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-10",
    },
    
    # ============================================================================
    # TEMPERATURE
    # ============================================================================
    "bms_max_cell_temp": {
        "name": "Max Cell Temperature",
        "key": "bmsMaxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_min_cell_temp": {
        "name": "Min Cell Temperature",
        "key": "bmsMinCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_max_mos_temp": {
        "name": "Max MOS Temperature",
        "key": "bmsMaxMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "bms_min_mos_temp": {
        "name": "Min MOS Temperature",
        "key": "bmsMinMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    
    # ============================================================================
    # POWER - Input
    # ============================================================================
    "pow_in_sum_w": {
        "name": "Total Input Power",
        "key": "powInSumW",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-import",
    },
    "pow_get_ac_in": {
        "name": "AC Input Power",
        "key": "powGetAcIn",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-plug",
    },
    "pow_get_pv_h": {
        "name": "Solar HV Input Power",
        "key": "powGetPvH",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "pow_get_pv_l": {
        "name": "Solar LV Input Power",
        "key": "powGetPvL",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "pow_get_5p8": {
        "name": "5.8V Input Power",
        "key": "powGet5p8",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "pow_get_4p81": {
        "name": "4.8V Port 1 Power",
        "key": "powGet4p81",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "pow_get_4p82": {
        "name": "4.8V Port 2 Power",
        "key": "powGet4p82",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    
    # ============================================================================
    # POWER - Output
    # ============================================================================
    "pow_out_sum_w": {
        "name": "Total Output Power",
        "key": "powOutSumW",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-export",
    },
    "pow_get_ac_hv_out": {
        "name": "AC HV Output Power",
        "key": "powGetAcHvOut",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "pow_get_ac_lv_out": {
        "name": "AC LV Output Power",
        "key": "powGetAcLvOut",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "pow_get_ac_lv_tt30_out": {
        "name": "AC LV TT30 Output Power",
        "key": "powGetAcLvTt30Out",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "pow_get_12v": {
        "name": "12V DC Output Power",
        "key": "powGet12v",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "pow_get_24v": {
        "name": "24V DC Output Power",
        "key": "powGet24v",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "pow_get_qcusb1": {
        "name": "QC USB 1 Output Power",
        "key": "powGetQcusb1",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pow_get_qcusb2": {
        "name": "QC USB 2 Output Power",
        "key": "powGetQcusb2",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pow_get_typec1": {
        "name": "Type-C 1 Output Power",
        "key": "powGetTypec1",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "pow_get_typec2": {
        "name": "Type-C 2 Output Power",
        "key": "powGetTypec2",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    
    # ============================================================================
    # AC SYSTEM
    # ============================================================================
    "ac_out_freq": {
        "name": "AC Output Frequency",
        "key": "acOutFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "plug_in_info_ac_in_feq": {
        "name": "AC Input Frequency",
        "key": "plugInInfoAcInFeq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "plug_in_info_ac_in_chg_pow_max": {
        "name": "AC Input Max Charge Power",
        "key": "plugInInfoAcInChgPowMax",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    "plug_in_info_ac_in_chg_hal_pow_max": {
        "name": "AC Input Hardware Max Charge Power",
        "key": "plugInInfoAcInChgHalPowMax",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    "plug_in_info_ac_out_dsg_pow_max": {
        "name": "AC Output Max Discharge Power",
        "key": "plugInInfoAcOutDsgPowMax",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    
    # ============================================================================
    # SOLAR (PV) SYSTEM
    # ============================================================================
    "plug_in_info_pv_h_chg_amp_max": {
        "name": "Solar HV Max Charge Current",
        "key": "plugInInfoPvHChgAmpMax",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "plug_in_info_pv_h_dc_amp_max": {
        "name": "Solar HV Max DC Current",
        "key": "plugInInfoPvHDcAmpMax",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "plug_in_info_pv_h_chg_vol_max": {
        "name": "Solar HV Max Charge Voltage",
        "key": "plugInInfoPvHChgVolMax",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "plug_in_info_pv_l_chg_amp_max": {
        "name": "Solar LV Max Charge Current",
        "key": "plugInInfoPvLChgAmpMax",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "plug_in_info_pv_l_dc_amp_max": {
        "name": "Solar LV Max DC Current",
        "key": "plugInInfoPvLDcAmpMax",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "plug_in_info_pv_l_chg_vol_max": {
        "name": "Solar LV Max Charge Voltage",
        "key": "plugInInfoPvLChgVolMax",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    
    # ============================================================================
    # PLUG-IN INFO - Extra Batteries
    # ============================================================================
    "plug_in_info_dcp2_sn": {
        "name": "Extra Battery 2 Serial Number",
        "key": "plugInInfoDcp2Sn",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:battery-plus",
    },
    "plug_in_info_dcp_sn": {
        "name": "Extra Battery Serial Number",
        "key": "plugInInfoDcpSn",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:battery-plus",
    },
    
    # ============================================================================
    # FLOW INFO - Connection Status
    # ============================================================================
    "flow_info_ac_hv_out": {
        "name": "AC HV Output Flow Status",
        "key": "flowInfoAcHvOut",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_ac_lv_out": {
        "name": "AC LV Output Flow Status",
        "key": "flowInfoAcLvOut",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_ac_in": {
        "name": "AC Input Flow Status",
        "key": "flowInfoAcIn",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_pv_h": {
        "name": "Solar HV Flow Status",
        "key": "flowInfoPvH",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_pv_l": {
        "name": "Solar LV Flow Status",
        "key": "flowInfoPvL",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_12v": {
        "name": "12V DC Flow Status",
        "key": "flowInfo12v",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_24v": {
        "name": "24V DC Flow Status",
        "key": "flowInfo24v",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_qcusb1": {
        "name": "QC USB 1 Flow Status",
        "key": "flowInfoQcusb1",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_qcusb2": {
        "name": "QC USB 2 Flow Status",
        "key": "flowInfoQcusb2",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_typec1": {
        "name": "Type-C 1 Flow Status",
        "key": "flowInfoTypec1",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    "flow_info_typec2": {
        "name": "Type-C 2 Flow Status",
        "key": "flowInfoTypec2",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["disconnected", "connected", "active"],
    },
    
    # ============================================================================
    # SETTINGS & TIMERS
    # ============================================================================
    "ac_standby_time": {
        "name": "AC Standby Time",
        "key": "acStandbyTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "dc_standby_time": {
        "name": "DC Standby Time",
        "key": "dcStandbyTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "ble_standby_time": {
        "name": "Bluetooth Standby Time",
        "key": "bleStandbyTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "screen_off_time": {
        "name": "Screen Off Time",
        "key": "screenOffTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:monitor-off",
    },
    "lcd_light": {
        "name": "LCD Brightness",
        "key": "lcdLight",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:brightness-6",
    },
    "backup_reverse_soc": {
        "name": "Backup Reserve SOC",
        "key": "backupReverseSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-lock",
    },
    
    # ============================================================================
    # GENERATOR & ENERGY STRATEGY
    # ============================================================================
    "cms_oil_on_soc": {
        "name": "Generator Start SOC",
        "key": "cmsOilOnSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine",
    },
    "cms_oil_off_soc": {
        "name": "Generator Stop SOC",
        "key": "cmsOilOffSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine-off",
    },
    "generator_care_mode_start_time": {
        "name": "Generator Care Mode Start Time",
        "key": "generatorCareModeStartTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:clock-start",
    },
    "generator_pv_hybrid_mode_soc_max": {
        "name": "Generator PV Hybrid Max SOC",
        "key": "generatorPvHybridModeSocMax",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    
    # ============================================================================
    # ERROR CODES & STATUS
    # ============================================================================
    "errcode": {
        "name": "Error Code",
        "key": "errcode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    "mppt_err_code": {
        "name": "MPPT Error Code",
        "key": "mpptErrCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    "dev_sleep_state": {
        "name": "Device Sleep State",
        "key": "devSleepState",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:sleep",
    },
    "dev_standby_time": {
        "name": "Device Standby Time",
        "key": "devStandbyTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "llc_hv_lv_flag": {
        "name": "LLC HV/LV Flag",
        "key": "llcHvLvFlag",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:flag",
    },
    "pcs_fan_level": {
        "name": "PCS Fan Level",
        "key": "pcsFanLevel",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:fan",
    },
    "multi_bp_chg_dsg_mode": {
        "name": "Multi Battery Pack Mode",
        "key": "multiBpChgDsgMode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:battery-sync",
    },
    
    # ============================================================================
    # TIMEZONE & TIME
    # ============================================================================
    "utc_timezone": {
        "name": "UTC Timezone Offset",
        "key": "utcTimezone",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:clock-outline",
    },
    "utc_timezone_id": {
        "name": "Timezone ID",
        "key": "utcTimezoneId",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:map-clock",
    },
    "quota_cloud_ts": {
        "name": "Cloud Timestamp",
        "key": "quota_cloud_ts",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "state_class": None,
        "icon": "mdi:cloud-clock",
    },
    "quota_device_ts": {
        "name": "Device Timestamp",
        "key": "quota_device_ts",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "state_class": None,
        "icon": "mdi:clock-digital",
    },
}


# Map device types to their sensor definitions
DEVICE_SENSOR_MAP = {
    "DELTA Pro 3": DELTA_PRO_3_SENSOR_DEFINITIONS,
    # Add other device types here as needed
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensors from a config entry."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get device type from config
    device_type = entry.data.get("device_type", "DELTA Pro 3")
    
    # Get sensor definitions for this device type
    sensor_definitions = DEVICE_SENSOR_MAP.get(device_type, DELTA_PRO_3_SENSOR_DEFINITIONS)
    
    # Create sensor entities
    entities = []
    for sensor_id, sensor_config in sensor_definitions.items():
        entities.append(
            EcoFlowSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id=sensor_id,
                sensor_config=sensor_config,
            )
        )
    
    # Add MQTT status sensors if using hybrid coordinator
    if isinstance(coordinator, EcoFlowHybridCoordinator):
        entities.append(
            EcoFlowMQTTStatusSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id="mqtt_connection_status",
            )
        )
        entities.append(
            EcoFlowMQTTModeSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id="connection_mode",
            )
        )
        _LOGGER.info("Added MQTT status sensors for hybrid coordinator")
    
    async_add_entities(entities)
    _LOGGER.info("Added %d sensor entities for %s", len(entities), device_type)


class EcoFlowSensor(EcoFlowBaseEntity, SensorEntity):
    """Representation of an EcoFlow sensor."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._sensor_id = sensor_id
        self._sensor_config = sensor_config
        self._attr_unique_id = f"{entry.entry_id}_{sensor_id}"
        self._attr_translation_key = sensor_id
        
        # Set sensor attributes from config
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")
        self._attr_icon = sensor_config.get("icon")
        
        # For ENUM sensors, set options
        if sensor_config.get("device_class") == SensorDeviceClass.ENUM:
            self._attr_options = sensor_config.get("options", [])

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        # Get the API key for this sensor
        api_key = self._sensor_config["key"]
        value = self.coordinator.data.get(api_key)
        
        if value is None:
            return None
        
        # Handle special cases
        # Timestamp sensors - convert string to datetime
        if self._attr_device_class == SensorDeviceClass.TIMESTAMP:
            # Skip if value is 0 or invalid (device not synced yet)
            if value == 0 or value == "0":
                return None
            if isinstance(value, str):
                try:
                    # Parse timestamp string and make it timezone aware
                    dt = datetime.fromisoformat(value.replace(' ', 'T'))
                    # If no timezone, assume UTC
                    if dt.tzinfo is None:
                        dt = dt_util.as_utc(dt)
                    return dt
                except (ValueError, AttributeError) as e:
                    _LOGGER.warning("Failed to parse timestamp '%s': %s", value, e)
                    return None
            # If it's already a datetime, return it
            if isinstance(value, datetime):
                return value
            # For any other type (int, etc.), return None
            return None
        
        # Flow info status mapping
        if api_key.startswith("flowInfo"):
            flow_map = {0: "disconnected", 1: "connected", 2: "active"}
            return flow_map.get(value, "disconnected")
        
        # Charge/discharge state mapping
        if api_key in ["bmsChgDsgState", "cmsChgDsgState"]:
            state_map = {0: "idle", 1: "charging", 2: "discharging"}
            return state_map.get(value, "idle")
        
        # Convert boolean to string for text sensors
        if isinstance(value, bool):
            return "on" if value else "off"
        
        return value


class EcoFlowMQTTStatusSensor(EcoFlowBaseEntity, SensorEntity):
    """Sensor for MQTT connection status."""
    
    def __init__(
        self,
        coordinator: EcoFlowHybridCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
    ) -> None:
        """Initialize MQTT status sensor."""
        super().__init__(coordinator, sensor_id)
        self._coordinator = coordinator
        self._attr_name = "MQTT Connection Status"
        self._attr_unique_id = f"{entry.entry_id}_mqtt_connection_status"
        self._attr_icon = "mdi:cloud-check"
        
    @property
    def native_value(self) -> str:
        """Return MQTT connection status."""
        if self._coordinator.mqtt_connected:
            return "connected"
        return "disconnected"
    
    @property
    def icon(self) -> str:
        """Return icon based on connection status."""
        if self._coordinator.mqtt_connected:
            return "mdi:cloud-check"
        return "mdi:cloud-off"


class EcoFlowMQTTModeSensor(EcoFlowBaseEntity, SensorEntity):
    """Sensor for connection mode (hybrid/rest_only)."""
    
    def __init__(
        self,
        coordinator: EcoFlowHybridCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
    ) -> None:
        """Initialize connection mode sensor."""
        super().__init__(coordinator, sensor_id)
        self._coordinator = coordinator
        self._attr_name = "Connection Mode"
        self._attr_unique_id = f"{entry.entry_id}_connection_mode"
        self._attr_icon = "mdi:connection"
        
    @property
    def native_value(self) -> str:
        """Return connection mode."""
        return self._coordinator.connection_mode
    
    @property
    def icon(self) -> str:
        """Return icon based on connection mode."""
        mode = self._coordinator.connection_mode
        if mode == "hybrid":
            return "mdi:connection"
        elif mode == "mqtt_standby":
            return "mdi:cloud-sync"
        return "mdi:cloud-off"
