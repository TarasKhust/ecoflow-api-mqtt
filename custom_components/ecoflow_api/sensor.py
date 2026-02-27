"""Sensor platform for EcoFlow API integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DEVICE_TYPE_DELTA_2,
    DEVICE_TYPE_SMART_PLUG,
    DEVICE_TYPE_STREAM_ULTRA_X,
    DOMAIN,
)
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
    "bms_cycles": {
        "name": "Battery Cycles",
        "key": "cycles",  # MQTT field name
        "unit": "cycles",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sync",
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
    # BMS Detailed Temperature Sensors (from BMS heartbeat - without prefix)
    "max_cell_temp": {
        "name": "BMS Max Cell Temp",
        "key": "maxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_cell_temp": {
        "name": "BMS Min Cell Temp",
        "key": "minCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "max_mos_temp": {
        "name": "BMS Max MOS Temp",
        "key": "maxMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_mos_temp": {
        "name": "BMS Min MOS Temp",
        "key": "minMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "max_env_temp": {
        "name": "Max Environment Temp",
        "key": "maxEnvTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_env_temp": {
        "name": "Min Environment Temp",
        "key": "minEnvTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "max_cur_sensor_temp": {
        "name": "Max Current Sensor Temp",
        "key": "maxCurSensorTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_cur_sensor_temp": {
        "name": "Min Current Sensor Temp",
        "key": "minCurSensorTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "bms_temp": {
        "name": "BMS Temperature",
        "key": "temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    # PCS/LLC/Inverter Temperature Sensors
    "inv_ntc_temp_2": {
        "name": "Inverter NTC Temp 2",
        "key": "invNtcTemp2",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "inv_ntc_temp_3": {
        "name": "Inverter NTC Temp 3",
        "key": "invNtcTemp3",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "ads_ntc_temp": {
        "name": "ADS NTC Temperature",
        "key": "adsNtcTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "llc_ntc_temp": {
        "name": "LLC NTC Temperature",
        "key": "llcNtcTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "temp_pv_h": {
        "name": "Solar HV Temperature",
        "key": "tempPvH",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "temp_pv_l": {
        "name": "Solar LV Temperature",
        "key": "tempPvL",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "temp_pcs_ac": {
        "name": "PCS AC Temperature",
        "key": "tempPcsAc",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "temp_pcs_dc": {
        "name": "PCS DC Temperature",
        "key": "tempPcsDc",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
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
    # Extra Battery 1 (Port 4P81) - decoded from resvInfo
    "extra_battery_1_soc": {
        "name": "Extra Battery 1 SOC",
        "key": "plugInInfo4p81Resv.resvInfo",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "resv_index": 0,
        "resv_type": "float",
    },
    "extra_battery_1_soh": {
        "name": "Extra Battery 1 SOH",
        "key": "plugInInfo4p81Resv.resvInfo",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
        "resv_index": 1,
        "resv_type": "float",
    },
    "extra_battery_1_design_capacity": {
        "name": "Extra Battery 1 Design Capacity",
        "key": "plugInInfo4p81Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
        "resv_index": 3,
        "resv_type": "mah_to_ah",
    },
    "extra_battery_1_full_capacity": {
        "name": "Extra Battery 1 Full Capacity",
        "key": "plugInInfo4p81Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
        "resv_index": 4,
        "resv_type": "mah_to_ah",
    },
    "extra_battery_1_remain_capacity": {
        "name": "Extra Battery 1 Remain Capacity",
        "key": "plugInInfo4p81Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-medium",
        "resv_index": 5,
        "resv_type": "mah_to_ah",
    },
    # Extra Battery 2 (Port 4P82) - decoded from resvInfo
    "extra_battery_2_soc": {
        "name": "Extra Battery 2 SOC",
        "key": "plugInInfo4p82Resv.resvInfo",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "resv_index": 0,
        "resv_type": "float",
    },
    "extra_battery_2_soh": {
        "name": "Extra Battery 2 SOH",
        "key": "plugInInfo4p82Resv.resvInfo",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
        "resv_index": 1,
        "resv_type": "float",
    },
    "extra_battery_2_design_capacity": {
        "name": "Extra Battery 2 Design Capacity",
        "key": "plugInInfo4p82Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
        "resv_index": 3,
        "resv_type": "mah_to_ah",
    },
    "extra_battery_2_full_capacity": {
        "name": "Extra Battery 2 Full Capacity",
        "key": "plugInInfo4p82Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
        "resv_index": 4,
        "resv_type": "mah_to_ah",
    },
    "extra_battery_2_remain_capacity": {
        "name": "Extra Battery 2 Remain Capacity",
        "key": "plugInInfo4p82Resv.resvInfo",
        "unit": "Ah",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-medium",
        "resv_index": 5,
        "resv_type": "mah_to_ah",
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
        "unit": "min",
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


# ============================================================================
# DELTA PRO (Original) Sensor Definitions
# Based on EcoFlow Developer API documentation
# ============================================================================

DELTA_PRO_SENSOR_DEFINITIONS = {
    # ============================================================================
    # BMS Master - Battery Management System
    # ============================================================================
    "bms_soc": {
        "name": "Battery Level",
        "key": "bmsMaster.soc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_temp": {
        "name": "Battery Temperature",
        "key": "bmsMaster.temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_input_watts": {
        "name": "Battery Input Power",
        "key": "bmsMaster.inputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "bms_output_watts": {
        "name": "Battery Output Power",
        "key": "bmsMaster.outputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "bms_vol": {
        "name": "Battery Voltage",
        "key": "bmsMaster.vol",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_amp": {
        "name": "Battery Current",
        "key": "bmsMaster.amp",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_soh": {
        "name": "Battery Health",
        "key": "bmsMaster.soh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "bms_design_cap": {
        "name": "Design Capacity",
        "key": "bmsMaster.designCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "bms_remain_cap": {
        "name": "Remaining Capacity",
        "key": "bmsMaster.remainCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "bms_full_cap": {
        "name": "Full Capacity",
        "key": "bmsMaster.fullCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "bms_max_cell_temp": {
        "name": "Max Cell Temperature",
        "key": "bmsMaster.maxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "bms_min_cell_temp": {
        "name": "Min Cell Temperature",
        "key": "bmsMaster.minCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "bms_remain_time": {
        "name": "Battery Remaining Time",
        "key": "bmsMaster.remainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "bms_err_code": {
        "name": "BMS Error Code",
        "key": "bmsMaster.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # Inverter
    # ============================================================================
    "inv_input_watts": {
        "name": "Inverter Input Power",
        "key": "inv.inputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-plug",
    },
    "inv_output_watts": {
        "name": "Inverter Output Power",
        "key": "inv.outputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "inv_out_freq": {
        "name": "AC Output Frequency",
        "key": "inv.invOutFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "inv_ac_in_freq": {
        "name": "AC Input Frequency",
        "key": "inv.acInFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "inv_out_temp": {
        "name": "Inverter Temperature",
        "key": "inv.outTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_dc_in_temp": {
        "name": "DC Input Temperature",
        "key": "inv.dcInTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_cfg_slow_chg_watts": {
        "name": "AC Slow Charging Power",
        "key": "inv.cfgSlowChgWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    "inv_cfg_standby_min": {
        "name": "AC Standby Time",
        "key": "inv.cfgStandbyMin",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "inv_err_code": {
        "name": "Inverter Error Code",
        "key": "inv.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # MPPT - Solar Charger
    # ============================================================================
    "mppt_in_watts": {
        "name": "Solar Input Power",
        "key": "mppt.inWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "mppt_out_watts": {
        "name": "MPPT Output Power",
        "key": "mppt.outWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "mppt_temp": {
        "name": "MPPT Temperature",
        "key": "mppt.mpptTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_dc12v_watts": {
        "name": "DC 12V Output Power",
        "key": "mppt.dcdc12vWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car-battery",
    },
    "mppt_car_out_watts": {
        "name": "Car Charger Output Power",
        "key": "mppt.carOutWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "mppt_car_temp": {
        "name": "Car Charger Temperature",
        "key": "mppt.carTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_fault_code": {
        "name": "MPPT Fault Code",
        "key": "mppt.faultCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # PD - Power Distribution
    # ============================================================================
    "pd_soc": {
        "name": "Display SOC",
        "key": "pd.soc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "pd_watts_out_sum": {
        "name": "Total Output Power",
        "key": "pd.wattsOutSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-export",
    },
    "pd_watts_in_sum": {
        "name": "Total Input Power",
        "key": "pd.wattsInSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-import",
    },
    "pd_remain_time": {
        "name": "Remaining Time",
        "key": "pd.remainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "pd_usb1_watts": {
        "name": "USB 1 Output Power",
        "key": "pd.usb1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-port",
    },
    "pd_usb2_watts": {
        "name": "USB 2 Output Power",
        "key": "pd.usb2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-port",
    },
    "pd_qc_usb1_watts": {
        "name": "QC USB 1 Output Power",
        "key": "pd.qcUsb1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-port",
    },
    "pd_qc_usb2_watts": {
        "name": "QC USB 2 Output Power",
        "key": "pd.qcUsb2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-port",
    },
    "pd_typec1_watts": {
        "name": "Type-C 1 Output Power",
        "key": "pd.typec1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "pd_typec2_watts": {
        "name": "Type-C 2 Output Power",
        "key": "pd.typec2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "pd_car_watts": {
        "name": "Car Output Power",
        "key": "pd.carWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "pd_standby_mode": {
        "name": "Device Standby Time",
        "key": "pd.standByMode",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer-sleep",
    },
    "pd_lcd_off_sec": {
        "name": "Screen Off Time",
        "key": "pd.lcdOffSec",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:monitor-off",
    },
    "pd_lcd_brightness": {
        "name": "Screen Brightness",
        "key": "pd.lcdBrightness",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:brightness-6",
    },
    "pd_chg_power_dc": {
        "name": "Cumulative DC Charged",
        "key": "pd.chgPowerDc",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-charging",
    },
    "pd_chg_sun_power": {
        "name": "Cumulative Solar Charged",
        "key": "pd.chgSunPower",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:solar-power",
    },
    "pd_chg_power_ac": {
        "name": "Cumulative AC Charged",
        "key": "pd.chgPowerAc",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:power-plug",
    },
    "pd_dsg_power_dc": {
        "name": "Cumulative DC Discharged",
        "key": "pd.dsgPowerDc",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-arrow-down",
    },
    "pd_dsg_power_ac": {
        "name": "Cumulative AC Discharged",
        "key": "pd.dsgPowerAc",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:power-socket",
    },
    "pd_err_code": {
        "name": "PD Error Code",
        "key": "pd.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    "pd_wifi_rssi": {
        "name": "WiFi Signal Strength",
        "key": "pd.wifiRssi",
        "unit": "dBm",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:wifi",
    },
    # ============================================================================
    # EMS - Energy Management System
    # ============================================================================
    "ems_max_charge_soc": {
        "name": "Max Charge Level",
        "key": "ems.maxChargeSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    "ems_min_dsg_soc": {
        "name": "Min Discharge Level",
        "key": "ems.minDsgSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-10",
    },
    "ems_min_open_oil_soc": {
        "name": "Generator Auto Start SOC",
        "key": "ems.minOpenOilEbSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine",
    },
    "ems_max_close_oil_soc": {
        "name": "Generator Auto Stop SOC",
        "key": "ems.maxCloseOilEbSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine-off",
    },
    "ems_chg_remain_time": {
        "name": "Charge Remaining Time",
        "key": "ems.chgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "ems_dsg_remain_time": {
        "name": "Discharge Remaining Time",
        "key": "ems.dsgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "ems_lcd_show_soc": {
        "name": "LCD Display SOC",
        "key": "ems.lcdShowSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
}

# NOTE: River 3, River 3 Plus and Delta 3 Plus are NOT supported by EcoFlow REST API
# These devices return error 1006. Removed from codebase.



# ============================================================================
# DELTA 2 - Sensor Definitions
# Based on EcoFlow Developer API documentation
# Uses unique data key format with prefixes: pd., bms_bmsStatus., bms_emsStatus., inv., mppt.
# ============================================================================
DELTA_2_SENSOR_DEFINITIONS = {
    # ============================================================================
    # Battery / BMS Sensors
    # ============================================================================
    "bms_soc": {
        "name": "Battery Level",
        "key": "bms_bmsStatus.soc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_soc_float": {
        "name": "Battery Level (Precise)",
        "key": "bms_bmsStatus.f32ShowSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_voltage": {
        "name": "Battery Voltage",
        "key": "bms_bmsStatus.vol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_current": {
        "name": "Battery Current",
        "key": "bms_bmsStatus.amp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_temp": {
        "name": "Battery Temperature",
        "key": "bms_bmsStatus.temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_cycles": {
        "name": "Battery Cycles",
        "key": "bms_bmsStatus.cycles",
        "unit": "cycles",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:sync",
    },
    "bms_design_cap": {
        "name": "Design Capacity",
        "key": "bms_bmsStatus.designCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "bms_full_cap": {
        "name": "Full Capacity",
        "key": "bms_bmsStatus.fullCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-high",
    },
    "bms_remain_cap": {
        "name": "Remaining Capacity",
        "key": "bms_bmsStatus.remainCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "bms_soh": {
        "name": "Battery Health",
        "key": "bms_bmsStatus.soh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "bms_max_cell_vol": {
        "name": "Max Cell Voltage",
        "key": "bms_bmsStatus.maxCellVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_min_cell_vol": {
        "name": "Min Cell Voltage",
        "key": "bms_bmsStatus.minCellVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_max_cell_temp": {
        "name": "Max Cell Temperature",
        "key": "bms_bmsStatus.maxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "bms_min_cell_temp": {
        "name": "Min Cell Temperature",
        "key": "bms_bmsStatus.minCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "bms_err_code": {
        "name": "BMS Error Code",
        "key": "bms_bmsStatus.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # Battery Power & State (Extended)
    # ============================================================================
    "bms_input_watts": {
        "name": "Battery Input Power",
        "key": "bms_bmsStatus.inputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "bms_output_watts": {
        "name": "Battery Output Power",
        "key": "bms_bmsStatus.outputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "bms_remain_time": {
        "name": "Battery Remaining Time",
        "key": "bms_bmsStatus.remainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "bms_chg_state": {
        "name": "Battery Charge State",
        "key": "bms_bmsStatus.chgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-sync",
        "options": ["not_charging", "charging"],
        "value_map": {0: "not_charging", 1: "charging"},
    },
    "bms_target_soc": {
        "name": "Battery Target SOC",
        "key": "bms_bmsStatus.targetSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    "bms_act_soc": {
        "name": "Battery Actual SOC",
        "key": "bms_bmsStatus.actSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "bms_balance_state": {
        "name": "Cell Balancing State",
        "key": "bms_bmsStatus.balanceState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:scale-balance",
        "options": ["not_balancing", "balancing"],
        "value_map": {0: "not_balancing", 1: "balancing"},
    },
    "bms_min_mos_temp": {
        "name": "Min MOS Temperature",
        "key": "bms_bmsStatus.minMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "bms_max_mos_temp": {
        "name": "Max MOS Temperature",
        "key": "bms_bmsStatus.maxMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "bms_real_soh": {
        "name": "Battery Real Health",
        "key": "bms_bmsStatus.realSoh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "bms_cyc_soh": {
        "name": "Battery Cycle Health",
        "key": "bms_bmsStatus.cycSoh",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart-variant",
    },
    "bms_mos_state": {
        "name": "MOS State",
        "key": "bms_bmsStatus.mosState",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:electric-switch",
    },
    "bms_fault": {
        "name": "BMS Fault",
        "key": "bms_bmsStatus.bmsFault",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    "bms_all_fault": {
        "name": "BMS All Faults",
        "key": "bms_bmsStatus.allBmsFault",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle-outline",
    },
    "bms_all_err_code": {
        "name": "BMS All Error Codes",
        "key": "bms_bmsStatus.allErrCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert",
    },
    # ============================================================================
    # Battery Info (Extended)
    # ============================================================================
    "bms_info_accu_chg_energy": {
        "name": "Total Charge Energy",
        "key": "bms_bmsInfo.accuChgEnergy",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-charging",
    },
    "bms_info_accu_dsg_energy": {
        "name": "Total Discharge Energy",
        "key": "bms_bmsInfo.accuDsgEnergy",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-arrow-down",
    },
    "bms_info_accu_chg_cap": {
        "name": "Total Charge Capacity",
        "key": "bms_bmsInfo.accuChgCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-plus",
    },
    "bms_info_accu_dsg_cap": {
        "name": "Total Discharge Capacity",
        "key": "bms_bmsInfo.accuDsgCap",
        "unit": "mAh",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:battery-minus",
    },
    "bms_info_round_trip": {
        "name": "Round Trip Efficiency",
        "key": "bms_bmsInfo.roundTrip",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:percent",
    },
    "bms_info_power_capability": {
        "name": "Power Capability",
        "key": "bms_bmsInfo.powerCapability",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "bms_info_deep_dsg_cnt": {
        "name": "Deep Discharge Count",
        "key": "bms_bmsInfo.deepDsgCnt",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter",
    },
    "bms_info_self_dsg_rate": {
        "name": "Self Discharge Rate",
        "key": "bms_bmsInfo.selfDsgRate",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down-outline",
    },
    "bms_info_soh": {
        "name": "Battery Info SOH",
        "key": "bms_bmsInfo.soh",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    # ============================================================================
    # Extra Battery 1 (bms_kitInfo.watts[0])
    # ============================================================================
    "extra_bat1_connected": {
        "name": "Extra Battery 1 Connected",
        "key": "bms_kitInfo.watts",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-plus",
        "kit_index": 0,
        "kit_field": "avaFlag",
        "options": ["disconnected", "connected"],
        "value_map": {0: "disconnected", 1: "connected"},
    },
    "extra_bat1_soc": {
        "name": "Extra Battery 1 Level",
        "key": "bms_kitInfo.watts",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "kit_index": 0,
        "kit_field": "soc",
    },
    "extra_bat1_soc_precise": {
        "name": "Extra Battery 1 Level (Precise)",
        "key": "bms_kitInfo.watts",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "kit_index": 0,
        "kit_field": "f32Soc",
    },
    "extra_bat1_power": {
        "name": "Extra Battery 1 Power",
        "key": "bms_kitInfo.watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
        "kit_index": 0,
        "kit_field": "curPower",
    },
    # ============================================================================
    # Extra Battery 2 (bms_kitInfo.watts[1])
    # ============================================================================
    "extra_bat2_connected": {
        "name": "Extra Battery 2 Connected",
        "key": "bms_kitInfo.watts",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-plus",
        "kit_index": 1,
        "kit_field": "avaFlag",
        "options": ["disconnected", "connected"],
        "value_map": {0: "disconnected", 1: "connected"},
    },
    "extra_bat2_soc": {
        "name": "Extra Battery 2 Level",
        "key": "bms_kitInfo.watts",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "kit_index": 1,
        "kit_field": "soc",
    },
    "extra_bat2_soc_precise": {
        "name": "Extra Battery 2 Level (Precise)",
        "key": "bms_kitInfo.watts",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "kit_index": 1,
        "kit_field": "f32Soc",
    },
    "extra_bat2_power": {
        "name": "Extra Battery 2 Power",
        "key": "bms_kitInfo.watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
        "kit_index": 1,
        "kit_field": "curPower",
    },
    # ============================================================================
    # EMS - Energy Management System (Charge Settings)
    # ============================================================================
    "ems_max_charge_soc": {
        "name": "Max Charge Level",
        "key": "bms_emsStatus.maxChargeSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    "ems_min_dsg_soc": {
        "name": "Min Discharge Level",
        "key": "bms_emsStatus.minDsgSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-10",
    },
    "ems_lcd_soc": {
        "name": "LCD Display SOC",
        "key": "bms_emsStatus.f32LcdShowSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "ems_chg_remain_time": {
        "name": "Charge Remaining Time",
        "key": "bms_emsStatus.chgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging",
    },
    "ems_dsg_remain_time": {
        "name": "Discharge Remaining Time",
        "key": "bms_emsStatus.dsgRemainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-arrow-down",
    },
    "ems_generator_on_soc": {
        "name": "Generator Auto Start SOC",
        "key": "bms_emsStatus.openOilSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine",
    },
    "ems_generator_off_soc": {
        "name": "Generator Auto Stop SOC",
        "key": "bms_emsStatus.closeOilSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:engine-off",
    },
    # ============================================================================
    # EMS - Extended Status
    # ============================================================================
    "ems_chg_amp": {
        "name": "EMS Charge Current",
        "key": "bms_emsStatus.chgAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "ems_chg_vol": {
        "name": "EMS Charge Voltage",
        "key": "bms_emsStatus.chgVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "ems_chg_state": {
        "name": "EMS Charge State",
        "key": "bms_emsStatus.chgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-charging",
        "options": ["not_charging", "charging"],
        "value_map": {0: "not_charging", 1: "charging"},
    },
    "ems_chg_cmd": {
        "name": "EMS Charge Command",
        "key": "bms_emsStatus.chgCmd",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-charging",
        "options": ["disabled", "enabled"],
        "value_map": {0: "disabled", 1: "enabled"},
    },
    "ems_dsg_cmd": {
        "name": "EMS Discharge Command",
        "key": "bms_emsStatus.dsgCmd",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-arrow-down",
        "options": ["disabled", "enabled"],
        "value_map": {0: "disabled", 1: "enabled"},
    },
    "ems_fan_level": {
        "name": "EMS Fan Level",
        "key": "bms_emsStatus.fanLevel",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:fan",
        "options": ["off", "level_1", "level_2", "level_3"],
        "value_map": {0: "off", 1: "level_1", 2: "level_2", 3: "level_3"},
    },
    "ems_open_ups_flag": {
        "name": "UPS Mode Enabled",
        "key": "bms_emsStatus.openUpsFlag",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-plug-battery",
        "options": ["disabled", "enabled"],
        "value_map": {0: "disabled", 1: "enabled"},
    },
    "ems_war_state": {
        "name": "EMS Warning State",
        "key": "bms_emsStatus.bmsWarState",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert",
        # bit0: hi_temp, bit1: low_temp, bit2: overload, bit3: chg_flag
    },
    "ems_is_normal_flag": {
        "name": "EMS Normal Status",
        "key": "bms_emsStatus.emsIsNormalFlag",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:check-circle",
        "options": ["sleep", "normal"],
        "value_map": {0: "sleep", 1: "normal"},
    },
    "ems_para_vol_min": {
        "name": "EMS Min Parallel Voltage",
        "key": "bms_emsStatus.paraVolMin",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "ems_para_vol_max": {
        "name": "EMS Max Parallel Voltage",
        "key": "bms_emsStatus.paraVolMax",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "ems_chg_line_plug": {
        "name": "Charge Line Plugged",
        "key": "bms_emsStatus.chgLinePlug",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-plug",
        "options": ["unplugged", "plugged"],
        "value_map": {0: "unplugged", 1: "plugged"},
    },
    # ============================================================================
    # PD - Power Distribution (Input/Output)
    # ============================================================================
    "pd_soc": {
        "name": "Display SOC",
        "key": "pd.soc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "pd_watts_in_sum": {
        "name": "Total Input Power",
        "key": "pd.wattsInSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-import",
    },
    "pd_watts_out_sum": {
        "name": "Total Output Power",
        "key": "pd.wattsOutSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower-export",
    },
    "pd_remain_time": {
        "name": "Remaining Time",
        "key": "pd.remainTime",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "pd_usb1_watts": {
        "name": "USB-A 1 Power",
        "key": "pd.usb1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pd_usb2_watts": {
        "name": "USB-A 2 Power",
        "key": "pd.usb2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pd_qc_usb1_watts": {
        "name": "QC USB 1 Power",
        "key": "pd.qcUsb1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pd_qc_usb2_watts": {
        "name": "QC USB 2 Power",
        "key": "pd.qcUsb2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb",
    },
    "pd_typec1_watts": {
        "name": "USB-C 1 Power",
        "key": "pd.typec1Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "pd_typec2_watts": {
        "name": "USB-C 2 Power",
        "key": "pd.typec2Watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:usb-c-port",
    },
    "pd_typec1_temp": {
        "name": "USB-C 1 Temperature",
        "key": "pd.typec1Temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "pd_typec2_temp": {
        "name": "USB-C 2 Temperature",
        "key": "pd.typec2Temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "pd_car_watts": {
        "name": "Car Output Power",
        "key": "pd.carWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "pd_car_temp": {
        "name": "Car Output Temperature",
        "key": "pd.carTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "pd_standby_min": {
        "name": "Device Standby Time",
        "key": "pd.standbyMin",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer-sleep",
    },
    "pd_lcd_off_sec": {
        "name": "Screen Timeout",
        "key": "pd.lcdOffSec",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:monitor-off",
    },
    "pd_bright_level": {
        "name": "Screen Brightness",
        "key": "pd.brightLevel",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:brightness-6",
    },
    "pd_err_code": {
        "name": "PD Error Code",
        "key": "pd.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    "pd_wifi_rssi": {
        "name": "WiFi Signal Strength",
        "key": "pd.wifiRssi",
        "unit": "dBm",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:wifi",
    },
    # ============================================================================
    # External Ports Status
    # ============================================================================
    "pd_ext_rj45_port": {
        "name": "RJ45 Port Status",
        "key": "pd.extRj45Port",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:ethernet",
        "options": ["null", "rc_ble_ctl"],
        "value_map": {0: "null", 1: "rc_ble_ctl"},
    },
    "pd_ext_3p8_port": {
        "name": "Right Port Status (3+8)",
        "key": "pd.ext3p8Port",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["null", "cc", "pr", "sp_bc"],
        "value_map": {0: "null", 1: "cc", 2: "pr", 3: "sp_bc"},
    },
    "pd_ext_4p8_port": {
        "name": "Left Port Status (4+8)",
        "key": "pd.ext4p8Port",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:connection",
        "options": ["null", "extra_battery", "smart_generator"],
        "value_map": {0: "null", 1: "extra_battery", 2: "smart_generator"},
    },
    # ============================================================================
    # PD - Extended Power & Energy
    # ============================================================================
    "pd_chg_power_ac": {
        "name": "Cumulative AC Charge",
        "key": "pd.chgPowerAC",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:lightning-bolt",
    },
    "pd_chg_power_dc": {
        "name": "Cumulative DC Charge",
        "key": "pd.chgPowerDC",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:current-dc",
    },
    "pd_chg_sun_power": {
        "name": "Cumulative Solar Charge",
        "key": "pd.chgSunPower",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:solar-power",
    },
    "pd_dsg_power_ac": {
        "name": "Cumulative AC Discharge",
        "key": "pd.dsgPowerAC",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:power-socket",
    },
    "pd_dsg_power_dc": {
        "name": "Cumulative DC Discharge",
        "key": "pd.dsgPowerDC",
        "unit": UnitOfEnergy.WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:usb",
    },
    # ============================================================================
    # PD - Extended Status & Control
    # ============================================================================
    "pd_dc_out_state": {
        "name": "DC Output State",
        "key": "pd.dcOutState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:usb",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "pd_car_state": {
        "name": "Car Output State",
        "key": "pd.carState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:car",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "pd_ac_enabled": {
        "name": "AC Output Enabled",
        "key": "pd.acEnabled",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-socket",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "pd_chg_dsg_state": {
        "name": "Charge/Discharge State",
        "key": "pd.chgDsgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-sync",
        "options": ["idle", "discharging", "charging"],
        "value_map": {0: "idle", 1: "discharging", 2: "charging"},
    },
    "pd_beep_mode": {
        "name": "Beep Mode",
        "key": "pd.beepMode",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:volume-high",
        "options": ["normal", "silent"],
        "value_map": {0: "normal", 1: "silent"},
    },
    "pd_charger_type": {
        "name": "Charger Type",
        "key": "pd.chargerType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:ev-plug-type2",
        "options": ["none", "ac", "dc_adapter", "solar", "cc", "bc"],
        "value_map": {0: "none", 1: "ac", 2: "dc_adapter", 3: "solar", 4: "cc", 5: "bc"},
    },
    "pd_bp_power_soc": {
        "name": "Backup Reserve Level",
        "key": "pd.bpPowerSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-lock",
    },
    "pd_min_ac_out_soc": {
        "name": "Min AC Output SOC",
        "key": "pd.minAcoutSoc",
        "unit": PERCENTAGE,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-alert",
    },
    "pd_pv_chg_prio_set": {
        "name": "Solar Charge Priority",
        "key": "pd.pvChgPrioSet",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:solar-power",
        "options": ["not_prioritized", "prioritized"],
        "value_map": {0: "not_prioritized", 1: "prioritized"},
    },
    # ============================================================================
    # PD - Usage Time Statistics
    # ============================================================================
    "pd_inv_used_time": {
        "name": "Inverter Used Time",
        "key": "pd.invUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "pd_mppt_used_time": {
        "name": "MPPT Used Time",
        "key": "pd.mpptUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "pd_car_used_time": {
        "name": "Car Output Used Time",
        "key": "pd.carUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "pd_usb_used_time": {
        "name": "USB Used Time",
        "key": "pd.usbUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "pd_typec_used_time": {
        "name": "USB-C Used Time",
        "key": "pd.typecUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    "pd_dc_in_used_time": {
        "name": "DC Input Used Time",
        "key": "pd.dcInUsedTime",
        "unit": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:timer",
    },
    # ============================================================================
    # INV - Inverter
    # ============================================================================
    "inv_input_watts": {
        "name": "AC Charging Power",
        "key": "inv.inputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-plug",
    },
    "inv_output_watts": {
        "name": "AC Discharging Power",
        "key": "inv.outputWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:power-socket",
    },
    "inv_out_vol": {
        "name": "AC Output Voltage",
        "key": "inv.invOutVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_out_amp": {
        "name": "AC Output Current",
        "key": "inv.invOutAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_out_freq": {
        "name": "AC Output Frequency",
        "key": "inv.invOutFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "inv_ac_in_vol": {
        "name": "AC Input Voltage",
        "key": "inv.acInVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_ac_in_amp": {
        "name": "AC Input Current",
        "key": "inv.acInAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_ac_in_freq": {
        "name": "AC Input Frequency",
        "key": "inv.acInFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "inv_out_temp": {
        "name": "Inverter Temperature",
        "key": "inv.outTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_standby_mins": {
        "name": "AC Standby Time",
        "key": "inv.standbyMins",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "inv_cfg_ac_out_freq": {
        "name": "AC Output Frequency Setting",
        "key": "inv.cfgAcOutFreq",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:sine-wave",
    },
    "inv_err_code": {
        "name": "Inverter Error Code",
        "key": "inv.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # INV - Extended
    # ============================================================================
    "inv_dc_in_vol": {
        "name": "DC Input Voltage",
        "key": "inv.dcInVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_dc_in_amp": {
        "name": "DC Input Current",
        "key": "inv.dcInAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_dc_in_temp": {
        "name": "DC Input Temperature",
        "key": "inv.dcInTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_fast_chg_watts": {
        "name": "Fast Charge Power",
        "key": "inv.FastChgWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "inv_slow_chg_watts": {
        "name": "Slow Charge Power",
        "key": "inv.SlowChgWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash-outline",
    },
    "inv_charger_type": {
        "name": "Inverter Charger Type",
        "key": "inv.chargerType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:ev-plug-type2",
        "options": ["none", "ac", "dc_adapter", "solar", "cc", "bc"],
        "value_map": {0: "none", 1: "ac", 2: "dc_adapter", 3: "solar", 4: "cc", 5: "bc"},
    },
    "inv_discharge_type": {
        "name": "Inverter Discharge Type",
        "key": "inv.dischargeType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-socket",
        "options": ["none", "ac", "pr", "bc"],
        "value_map": {0: "none", 1: "ac", 2: "pr", 3: "bc"},
    },
    "inv_fan_state": {
        "name": "Inverter Fan State",
        "key": "inv.fanState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:fan",
        "options": ["off", "level_1", "level_2", "level_3"],
        "value_map": {0: "off", 1: "level_1", 2: "level_2", 3: "level_3"},
    },
    "inv_cfg_ac_enabled": {
        "name": "AC Output Enabled Config",
        "key": "inv.cfgAcEnabled",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-socket",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "inv_cfg_ac_xboost": {
        "name": "X-Boost Enabled",
        "key": "inv.cfgAcXboost",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:rocket-launch",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "inv_cfg_ac_out_vol": {
        "name": "AC Output Voltage Config",
        "key": "inv.cfgAcOutVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "inv_cfg_ac_work_mode": {
        "name": "AC Work Mode",
        "key": "inv.cfgAcWorkMode",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:cog",
        "options": ["full_power", "mute"],
        "value_map": {0: "full_power", 1: "mute"},
    },
    "inv_chg_pause_flag": {
        "name": "Inverter Charge Pause",
        "key": "inv.chgPauseFlag",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:pause-circle",
        "options": ["normal", "paused"],
        "value_map": {0: "normal", 1: "paused"},
    },
    "inv_ac_dip_switch": {
        "name": "AC DIP Switch",
        "key": "inv.acDipSwitch",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:toggle-switch",
        "options": ["unknown", "fast_charging", "slow_charging"],
        "value_map": {0: "unknown", 1: "fast_charging", 2: "slow_charging"},
    },
    # ============================================================================
    # MPPT - Solar Charger
    # ============================================================================
    "mppt_in_watts": {
        "name": "Solar Input Power",
        "key": "mppt.inWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "mppt_in_vol": {
        "name": "Solar Input Voltage",
        "key": "mppt.inVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "mppt_in_amp": {
        "name": "Solar Input Current",
        "key": "mppt.inAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "mppt_out_watts": {
        "name": "MPPT Output Power",
        "key": "mppt.outWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "mppt_out_vol": {
        "name": "MPPT Output Voltage",
        "key": "mppt.outVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_out_amp": {
        "name": "MPPT Output Current",
        "key": "mppt.outAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_temp": {
        "name": "MPPT Temperature",
        "key": "mppt.mpptTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_dc12v_watts": {
        "name": "DC 12V Output Power",
        "key": "mppt.dcdc12vWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car-battery",
    },
    "mppt_dc12v_vol": {
        "name": "DC 12V Output Voltage",
        "key": "mppt.dcdc12vVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car-battery",
    },
    "mppt_dc12v_amp": {
        "name": "DC 12V Output Current",
        "key": "mppt.dcdc12vAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car-battery",
    },
    "mppt_car_out_watts": {
        "name": "Car Charger Output Power",
        "key": "mppt.carOutWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "mppt_car_out_vol": {
        "name": "Car Charger Output Voltage",
        "key": "mppt.carOutVol",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "mppt_car_out_amp": {
        "name": "Car Charger Output Current",
        "key": "mppt.carOutAmp",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:car",
    },
    "mppt_car_temp": {
        "name": "Car Charger Temperature",
        "key": "mppt.carTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_cfg_chg_watts": {
        "name": "AC Charging Power Limit",
        "key": "mppt.cfgChgWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:lightning-bolt",
    },
    "mppt_dc_chg_current": {
        "name": "DC Charging Current Limit",
        "key": "mppt.dcChgCurrent",
        "unit": UnitOfElectricCurrent.MILLIAMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-dc",
    },
    "mppt_ac_standby_mins": {
        "name": "AC Standby Time Setting",
        "key": "mppt.acStandbyMins",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "mppt_car_standby_min": {
        "name": "Car Standby Time Setting",
        "key": "mppt.carStandbyMin",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "mppt_fault_code": {
        "name": "MPPT Fault Code",
        "key": "mppt.faultCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
    },
    # ============================================================================
    # MPPT - Extended
    # ============================================================================
    "mppt_chg_type": {
        "name": "MPPT Charge Type",
        "key": "mppt.chgType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:flash",
        "options": ["null", "adapter", "mppt_solar", "ac", "gas", "wind"],
        "value_map": {0: "null", 1: "adapter", 2: "mppt_solar", 3: "ac", 4: "gas", 5: "wind"},
    },
    "mppt_chg_state": {
        "name": "MPPT Charge State",
        "key": "mppt.chgState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:battery-charging",
        "options": ["off", "charging", "standby"],
        "value_map": {0: "off", 1: "charging", 2: "standby"},
    },
    "mppt_chg_pause_flag": {
        "name": "MPPT Charge Pause",
        "key": "mppt.chgPauseFlag",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:pause-circle",
        "options": ["normal", "paused"],
        "value_map": {0: "normal", 1: "paused"},
    },
    "mppt_cfg_chg_type": {
        "name": "MPPT Charge Type Config",
        "key": "mppt.cfgChgType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:cog",
        "options": ["auto", "mppt", "adapter"],
        "value_map": {0: "auto", 1: "mppt", 2: "adapter"},
    },
    "mppt_car_state": {
        "name": "Car Charger State",
        "key": "mppt.carState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:car",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "mppt_discharge_type": {
        "name": "MPPT Discharge Type",
        "key": "mppt.dischargeType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-socket",
        "options": ["none", "ac", "pr", "bc"],
        "value_map": {0: "none", 1: "ac", 2: "pr", 3: "bc"},
    },
    "mppt_dc24v_state": {
        "name": "DC 24V State",
        "key": "mppt.dc24vState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:flash",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "mppt_dc24v_temp": {
        "name": "DC 24V Temperature",
        "key": "mppt.dc24vTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_beep_state": {
        "name": "MPPT Beep State",
        "key": "mppt.beepState",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:volume-high",
        "options": ["default", "silent"],
        "value_map": {0: "default", 1: "silent"},
    },
    "mppt_cfg_ac_enabled": {
        "name": "MPPT AC Enabled Config",
        "key": "mppt.cfgAcEnabled",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-socket",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "mppt_cfg_ac_xboost": {
        "name": "MPPT X-Boost Config",
        "key": "mppt.cfgAcXboost",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:rocket-launch",
        "options": ["off", "on"],
        "value_map": {0: "off", 1: "on"},
    },
    "mppt_cfg_ac_out_vol": {
        "name": "MPPT AC Output Voltage Config",
        "key": "mppt.cfgAcOutVol",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "mppt_cfg_ac_out_freq": {
        "name": "MPPT AC Output Frequency Config",
        "key": "mppt.cfgAcOutFreq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "mppt_scr_standby_min": {
        "name": "Screen Standby Time",
        "key": "mppt.scrStandbyMin",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "mppt_pow_standby_min": {
        "name": "Power Standby Time",
        "key": "mppt.powStandbyMin",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:timer",
    },
    "mppt_x60_chg_type": {
        "name": "XT60 Charge Type",
        "key": "mppt.x60ChgType",
        "unit": None,
        "device_class": SensorDeviceClass.ENUM,
        "state_class": None,
        "icon": "mdi:power-plug",
        "options": ["not_detected", "mppt", "adapter"],
        "value_map": {0: "not_detected", 1: "mppt", 2: "adapter"},
    },
}


# ============================================================================
# STREAM ULTRA X - Sensor Definitions
# Based on EcoFlow Developer API documentation for STREAM system (BKW)
# ============================================================================

STREAM_ULTRA_X_SENSOR_DEFINITIONS = {
    # ============================================================================
    # BATTERY
    # ============================================================================
    "battery_level": {
        "name": "Battery Level",
        "key": "cmsBattSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery",
    },
    "backup_reserve_level": {
        "name": "Backup Reserve Level",
        "key": "backupReverseSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-heart",
    },
    "max_charge_level": {
        "name": "Max Charge Level",
        "key": "cmsMaxChgSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-charging-100",
    },
    "min_discharge_level": {
        "name": "Min Discharge Level",
        "key": "cmsMinDsgSoc",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-low",
    },
    # ============================================================================
    # POWER - Real-time Power Flow
    # ============================================================================
    "solar_power": {
        "name": "Solar Input Power",
        "key": "powGetPvSum",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "system_load_power": {
        "name": "System Load Power",
        "key": "powGetSysLoad",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:home-lightning-bolt",
    },
    "grid_power": {
        "name": "Grid Power",
        "key": "powGetSysGrid",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower",
    },
    "grid_connection_power": {
        "name": "Grid Connection Power",
        "key": "gridConnectionPower",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:transmission-tower",
        # Positive = consuming from grid, Negative = feeding to grid
    },
    "battery_power": {
        "name": "Battery Power",
        "key": "powGetBpCms",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:battery-sync",
        # Positive = charging, Negative = discharging
    },
    # ============================================================================
    # SYSTEM STATUS
    # ============================================================================
    "feed_in_mode": {
        "name": "Feed-in Control",
        "key": "feedGridMode",
        "device_class": SensorDeviceClass.ENUM,
        "icon": "mdi:transmission-tower-export",
        "options": ["off", "on"],
        "value_map": {1: "off", 2: "on"},
    },
    "last_update": {
        "name": "Last Update",
        "key": "quota_cloud_ts",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "icon": "mdi:clock-outline",
    },
    # ============================================================================
    # TEMPERATURE
    # ============================================================================
    "battery_temperature": {
        "name": "Battery Temperature",
        "key": "temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "max_cell_temperature": {
        "name": "Max Cell Temperature",
        "key": "bmsMaxCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_cell_temperature": {
        "name": "Min Cell Temperature",
        "key": "bmsMinCellTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
    "max_mosfet_temperature": {
        "name": "Max MOSFET Temperature",
        "key": "bmsMaxMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-high",
    },
    "min_mosfet_temperature": {
        "name": "Min MOSFET Temperature",
        "key": "bmsMinMosTemp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer-low",
    },
}


# ============================================================================
# Smart Plug S401 Sensor Definitions
# Based on EcoFlow API documentation for Smart Plug
# Field prefix: 2_1. (heartbeat data)
# ============================================================================
SMART_PLUG_SENSOR_DEFINITIONS = {
    # ============================================================================
    # POWER MONITORING
    # ============================================================================
    "power": {
        "name": "Power",
        "key": "2_1.watts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "value_map": lambda x: x / 10 if x is not None else None,  # API returns 0.1W units
    },
    "voltage": {
        "name": "Voltage",
        "key": "2_1.volt",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "current": {
        "name": "Current",
        "key": "2_1.current",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
        "value_map": lambda x: x / 1000 if x is not None else None,  # API returns mA
    },
    # ============================================================================
    # DEVICE STATUS
    # ============================================================================
    "temperature": {
        "name": "Temperature",
        "key": "2_1.temp",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "frequency": {
        "name": "Frequency",
        "key": "2_1.freq",
        "unit": UnitOfFrequency.HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    "led_brightness": {
        "name": "LED Brightness",
        "key": "2_1.brightness",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:brightness-6",
        "value_map": lambda x: round((x / 1023) * 100) if x is not None else None,  # Convert 0-1023 to 0-100%
    },
    "max_current": {
        "name": "Maximum Current",
        "key": "2_1.maxCur",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
        "value_map": lambda x: x / 10 if x is not None else None,  # API returns 0.1A units
    },
    "overload_protection_threshold": {
        "name": "Overload Protection Threshold",
        "key": "2_1.maxWatts",
        "unit": UnitOfPower.WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:shield-alert",
    },
    # ============================================================================
    # DIAGNOSTICS
    # ============================================================================
    "error_code": {
        "name": "Error Code",
        "key": "2_1.errCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert-circle",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "warning_code": {
        "name": "Warning Code",
        "key": "2_1.warnCode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:alert",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "last_update": {
        "name": "Last Update",
        "key": "2_1.updateTime",
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "state_class": None,
        "icon": "mdi:clock-outline",
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
}


# Map device types to their sensor definitions
DEVICE_SENSOR_MAP = {
    "DELTA Pro 3": DELTA_PRO_3_SENSOR_DEFINITIONS,
    "Delta Pro": DELTA_PRO_SENSOR_DEFINITIONS,
    "Delta 2": DELTA_2_SENSOR_DEFINITIONS,
    "delta_pro_3": DELTA_PRO_3_SENSOR_DEFINITIONS,
    "delta_pro": DELTA_PRO_SENSOR_DEFINITIONS,
    DEVICE_TYPE_DELTA_2: DELTA_2_SENSOR_DEFINITIONS,
    DEVICE_TYPE_STREAM_ULTRA_X: STREAM_ULTRA_X_SENSOR_DEFINITIONS,
    "Stream Ultra X": STREAM_ULTRA_X_SENSOR_DEFINITIONS,
    DEVICE_TYPE_SMART_PLUG: SMART_PLUG_SENSOR_DEFINITIONS,
    "Smart Plug S401": SMART_PLUG_SENSOR_DEFINITIONS,
    "smart_plug": SMART_PLUG_SENSOR_DEFINITIONS,
}


# ============================================================================
# Energy Integration Sensors
# ============================================================================


class EcoFlowIntegralEnergySensor(IntegrationSensor):
    """Integration sensor that calculates energy (kWh) from power (W) sensors.

    Automatically integrates power sensors to provide energy consumption/generation
    compatible with Home Assistant Energy Dashboard.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_registry_visible_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        power_sensor: SensorEntity,
        enabled_default: bool = True,
    ):
        """Initialize energy sensor from power sensor."""
        super().__init__(
            hass=hass,
            integration_method="left",
            name=f"{power_sensor.name} Energy",
            round_digits=4,
            source_entity=power_sensor.entity_id,
            unique_id=f"{power_sensor.unique_id}_energy",
            unit_prefix="k",
            unit_time="h",
            max_sub_interval=timedelta(seconds=60),
        )
        # Copy device info from power sensor
        self._attr_device_info = power_sensor.device_info
        self._attr_entity_registry_enabled_default = enabled_default


class EcoFlowPowerDifferenceSensor(SensorEntity, EcoFlowBaseEntity):
    """Sensor that calculates power difference (input - output).

    Useful for Home Assistant Energy Dashboard to show net power flow.
    Positive = charging, Negative = discharging.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        input_sensor: SensorEntity,
        output_sensor: SensorEntity,
    ):
        """Initialize power difference sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_power_difference"
        self._attr_name = "Power Difference"
        self._attr_icon = "mdi:transmission-tower-export"

        self._input_sensor = input_sensor
        self._output_sensor = output_sensor
        self._difference: float | None = None
        self._states: dict[str, float | str] = {}

    async def async_added_to_hass(self) -> None:
        """Handle added to Hass."""
        await super().async_added_to_hass()

        source_entity_ids = [
            self._input_sensor.entity_id,
            self._output_sensor.entity_id,
        ]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                source_entity_ids,
                self._async_difference_sensor_state_listener,
            )
        )

        # Replay current state of source entities
        for entity_id in source_entity_ids:
            state = self.hass.states.get(entity_id)
            if state:
                state_event: Event[EventStateChangedData] = Event(
                    "", {"entity_id": entity_id, "new_state": state, "old_state": None}
                )
                self._async_difference_sensor_state_listener(
                    state_event, update_state=False
                )

        self._calc_difference()

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._difference

    @callback
    def _async_difference_sensor_state_listener(
        self, event: Event[EventStateChangedData], update_state: bool = True
    ) -> None:
        """Handle the sensor state changes."""
        new_state = event.data["new_state"]
        entity = event.data["entity_id"]

        if (
            new_state is None
            or new_state.state is None
            or new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]
        ):
            self._states[entity] = STATE_UNKNOWN
            if not update_state:
                return

            self._calc_difference()
            self.async_write_ha_state()
            return

        try:
            self._states[entity] = float(new_state.state)
        except ValueError:
            _LOGGER.warning(
                "Unable to store state for %s. Only numerical states are supported",
                entity,
            )
            return

        if not update_state:
            return

        self._calc_difference()
        self.async_write_ha_state()

    @callback
    def _calc_difference(self) -> None:
        """Calculate the power difference (input - output)."""
        if (
            self._states.get(self._input_sensor.entity_id) is STATE_UNKNOWN
            or self._states.get(self._output_sensor.entity_id) is STATE_UNKNOWN
        ):
            self._difference = None
            return

        # Power difference: input - output
        # Positive = charging/receiving power
        # Negative = discharging/consuming power
        input_power = float(self._states.get(self._input_sensor.entity_id, 0))
        output_power = float(self._states.get(self._output_sensor.entity_id, 0))
        self._difference = input_power - output_power


# ============================================================================
# Sensor Setup
# ============================================================================


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
    sensor_definitions = DEVICE_SENSOR_MAP.get(
        device_type, DELTA_PRO_3_SENSOR_DEFINITIONS
    )

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

    # ============================================================================
    # Add Energy Integration Sensors (for HA Energy Dashboard)
    # ============================================================================
    energy_sensors = []

    # Find total input and output power sensors
    total_input_sensor = None
    total_output_sensor = None

    for sensor in entities:
        if isinstance(sensor, EcoFlowSensor):
            # Total Input Power sensor (for energy dashboard)
            if sensor._sensor_id == "pow_in_sum_w":
                total_input_sensor = sensor
                # Add energy sensor for total input
                energy_sensors.append(
                    EcoFlowIntegralEnergySensor(hass, sensor, enabled_default=True)
                )

            # Total Output Power sensor (for energy dashboard)
            elif sensor._sensor_id == "pow_out_sum_w":
                total_output_sensor = sensor
                # Add energy sensor for total output
                energy_sensors.append(
                    EcoFlowIntegralEnergySensor(hass, sensor, enabled_default=True)
                )

            # AC Input Power (optional, disabled by default)
            elif sensor._sensor_id == "pow_get_ac_in":
                energy_sensors.append(
                    EcoFlowIntegralEnergySensor(hass, sensor, enabled_default=False)
                )

    # Add Power Difference Sensor (for HA Energy "Now" tab)
    if total_input_sensor and total_output_sensor:
        energy_sensors.append(
            EcoFlowPowerDifferenceSensor(
                coordinator=coordinator,
                entry=entry,
                input_sensor=total_input_sensor,
                output_sensor=total_output_sensor,
            )
        )
        _LOGGER.info("Created power difference sensor for energy dashboard")

    if energy_sensors:
        async_add_entities(energy_sensors)
        _LOGGER.info(
            "Added %d energy sensors for Home Assistant Energy Dashboard",
            len(energy_sensors),
        )


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
        self._attr_name = sensor_config.get("name", sensor_id)
        self._attr_has_entity_name = True

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

        # Handle nested object fallback for dotted keys (e.g., "plugInInfo4p81Resv.resvInfo")
        # The EcoFlow API/MQTT may return data as nested objects instead of flat dotted keys
        if value is None and "." in api_key:
            parts = api_key.split(".", 1)
            parent = self.coordinator.data.get(parts[0])
            if isinstance(parent, dict):
                value = parent.get(parts[1])

        # Try fallback key if primary key has no data
        if value is None or (isinstance(value, list) and all(v == 0 for v in value)):
            fallback_key = self._sensor_config.get("fallback_key")
            if fallback_key:
                value = self.coordinator.data.get(fallback_key)
                # Also try nested fallback for dotted fallback keys
                if value is None and "." in fallback_key:
                    parts = fallback_key.split(".", 1)
                    parent = self.coordinator.data.get(parts[0])
                    if isinstance(parent, dict):
                        value = parent.get(parts[1])
                if value is not None:
                    api_key = fallback_key  # Use fallback key for further processing

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
                    dt = datetime.fromisoformat(value.replace(" ", "T"))
                    # If no timezone, assume UTC (EcoFlow API timestamps are in UTC)
                    if dt.tzinfo is None:
                        dt = dt_util.as_utc(dt)
                    # Ensure it's timezone-aware UTC for proper local time conversion
                    if dt.tzinfo != dt_util.UTC:
                        dt = dt.astimezone(dt_util.UTC)
                    return dt
                except (ValueError, AttributeError) as e:
                    _LOGGER.warning("Failed to parse timestamp '%s': %s", value, e)
                    return None
            # If it's already a datetime, return it
            if isinstance(value, datetime):
                # Ensure it's timezone-aware UTC
                if value.tzinfo is None:
                    value = dt_util.as_utc(value)
                elif value.tzinfo != dt_util.UTC:
                    value = value.astimezone(dt_util.UTC)
                return value
            # Handle numeric timestamps (Unix timestamp in milliseconds or seconds)
            if isinstance(value, (int, float)):
                try:
                    # If timestamp is in milliseconds (> year 2000 in seconds), convert to seconds
                    if value > 946684800000:  # Year 2000 in milliseconds
                        value = value / 1000
                    # Convert to UTC datetime (Home Assistant will auto-convert to local time)
                    return dt_util.utc_from_timestamp(value)
                except (ValueError, OSError) as e:
                    _LOGGER.warning(
                        "Failed to convert numeric timestamp '%s': %s", value, e
                    )
                    return None
            # For any other type, return None
            return None

        # Flow info status mapping
        if api_key.startswith("flowInfo"):
            flow_map = {0: "disconnected", 1: "connected", 2: "active"}
            return flow_map.get(value, "disconnected")

        # Charge/discharge state mapping
        if api_key in ["bmsChgDsgState", "cmsChgDsgState"]:
            state_map = {0: "idle", 1: "discharging", 2: "charging"}
            return state_map.get(value, "idle")

        # Generic value_map handling
        value_map = self._sensor_config.get("value_map")
        if value_map:
            # If value_map is a function (lambda), call it for conversion
            if callable(value_map):
                return value_map(value)
            # If value_map is a dict, use it for ENUM mapping
            elif isinstance(value_map, dict) and isinstance(value, (int, float)):
                return value_map.get(int(value), value_map.get("default", str(value)))

        # Handle resvInfo array decoding for Extra Battery sensors
        if "resvInfo" in api_key and isinstance(value, list):
            resv_index = self._sensor_config.get("resv_index")
            resv_type = self._sensor_config.get("resv_type")
            if resv_index is not None and resv_index < len(value):
                raw_val = value[resv_index]
                if raw_val == 0:
                    return None  # No data available
                if resv_type == "float":
                    # Decode IEEE 754 float from int
                    import struct

                    try:
                        decoded = struct.unpack("f", struct.pack("I", raw_val))[0]
                        return round(decoded, 2)
                    except (struct.error, OverflowError):
                        return None
                elif resv_type == "mah_to_ah":
                    # Convert mAh to Ah
                    return round(raw_val / 1000, 2)
                else:
                    return raw_val
            return None

        # Handle bms_kitInfo.watts array for Extra Battery sensors (Delta 2)
        if "bms_kitInfo.watts" in api_key and isinstance(value, list):
            kit_index = self._sensor_config.get("kit_index")
            kit_field = self._sensor_config.get("kit_field")
            if kit_index is not None and kit_index < len(value):
                kit_data = value[kit_index]
                if isinstance(kit_data, dict):
                    # Check if battery is available (avaFlag > 0)
                    if kit_field == "avaFlag":
                        ava_flag = kit_data.get("avaFlag", 0)
                        # Return mapped value for ENUM
                        value_map = self._sensor_config.get("value_map")
                        if value_map:
                            return value_map.get(ava_flag, "unknown")
                        return ava_flag
                    # Only return data if battery is connected
                    if kit_data.get("avaFlag", 0) == 0:
                        return None
                    field_value = kit_data.get(kit_field)
                    if field_value is not None:
                        return field_value
            return None

        # UTC Timezone Offset - value is already in minutes from API
        # EcoFlow API returns timezone offset in minutes (e.g., 200 = 200 minutes = UTC+3:20)
        # We keep it as-is since it's already in the correct format
        if api_key == "utcTimezone":
            if isinstance(value, (int, float)):
                # If value is very large (> 1000), might be in seconds, convert to minutes
                if abs(value) > 1000:
                    value = value / 60
                # Return as integer minutes (value from API is already in minutes)
                return int(value)

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
