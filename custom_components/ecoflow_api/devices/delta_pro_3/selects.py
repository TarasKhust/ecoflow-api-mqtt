"""Delta Pro 3 select definitions."""

from __future__ import annotations

from ..base import EcoFlowSelectDef

SELECTS = [
    EcoFlowSelectDef(
        key="ac_standby_time",
        name="AC Standby Time",
        state_key="acStandbyTime",
        param_key="cfgAcStandbyTime",
        icon="mdi:timer",
        options={
            "Never": 0,
            "30 min": 30,
            "1 hour": 60,
            "2 hours": 120,
            "4 hours": 240,
            "6 hours": 360,
        },
    ),
    EcoFlowSelectDef(
        key="dc_standby_time",
        name="DC Standby Time",
        state_key="dcStandbyTime",
        param_key="cfgDcStandbyTime",
        icon="mdi:timer",
        options={
            "Never": 0,
            "30 min": 30,
            "1 hour": 60,
            "2 hours": 120,
            "4 hours": 240,
            "6 hours": 360,
        },
    ),
    EcoFlowSelectDef(
        key="battery_charge_mode",
        name="Battery Charge Mode",
        state_key="multiBpChgDsgMode",
        param_key="cfgMultiBpChgDsgMode",
        icon="mdi:battery-sync",
        options={
            "Default": 0,
            "Auto (by voltage)": 1,
            "Main priority charge, Extra priority discharge": 2,
        },
    ),
    EcoFlowSelectDef(
        key="ac_output_frequency",
        name="AC Output Frequency",
        state_key="acOutFreq",
        param_key="cfgAcOutFreq",
        icon="mdi:sine-wave",
        options={
            "50 Hz": 50,
            "60 Hz": 60,
        },
    ),
    EcoFlowSelectDef(
        key="energy_strategy_mode",
        name="Energy Strategy Mode",
        param_key="cfgEnergyStrategyOperateMode",
        icon="mdi:strategy",
        nested_params=True,
        options={
            "Off": "off",
            "Self-Powered": "self_powered",
            "TOU": "tou",
        },
    ),
]
