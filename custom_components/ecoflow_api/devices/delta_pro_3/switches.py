"""Delta Pro 3 switch definitions."""

from __future__ import annotations

from ..base import EcoFlowSwitchDef

SWITCHES = [
    EcoFlowSwitchDef(
        key="ac_hv_out",
        name="AC HV Output",
        state_key="flowInfoAcHvOut",
        param_key="cfgHvAcOutOpen",
        state_interpreter="flow_info",
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
    ),
    EcoFlowSwitchDef(
        key="ac_lv_out",
        name="AC LV Output",
        state_key="flowInfoAcLvOut",
        param_key="cfgLvAcOutOpen",
        state_interpreter="flow_info",
        icon_on="mdi:power-socket",
        icon_off="mdi:power-socket-off",
    ),
    EcoFlowSwitchDef(
        key="dc_12v_out",
        name="12V DC Output",
        state_key="flowInfo12v",
        param_key="cfgDc12vOutOpen",
        state_interpreter="flow_info",
        icon_on="mdi:current-dc",
        icon_off="mdi:power-off",
    ),
    EcoFlowSwitchDef(
        key="x_boost",
        name="X-Boost",
        state_key="xboostEn",
        param_key="cfgXboostEn",
        icon_on="mdi:lightning-bolt",
        icon_off="mdi:lightning-bolt-outline",
    ),
    EcoFlowSwitchDef(
        key="beeper",
        name="Beeper",
        state_key="enBeep",
        param_key="cfgBeepEn",
        icon_on="mdi:volume-high",
        icon_off="mdi:volume-off",
    ),
    EcoFlowSwitchDef(
        key="ac_energy_saving",
        name="AC Energy Saving",
        state_key="acEnergySavingOpen",
        param_key="cfgAcEnergySavingOpen",
        icon_on="mdi:leaf",
        icon_off="mdi:leaf-off",
    ),
    EcoFlowSwitchDef(
        key="generator_auto_start",
        name="Generator Auto Start",
        state_key="cmsOilSelfStart",
        param_key="cfgCmsOilSelfStart",
        icon_on="mdi:engine",
        icon_off="mdi:engine-off",
    ),
    EcoFlowSwitchDef(
        key="gfci",
        name="GFCI",
        state_key="llcGFCIFlag",
        param_key="cfgLlcGFCIFlag",
        icon_on="mdi:shield-check",
        icon_off="mdi:shield-off",
    ),
    EcoFlowSwitchDef(
        key="generator_pv_hybrid",
        name="Generator PV Hybrid Mode",
        state_key="generatorPvHybridModeOpen",
        param_key="cfgGeneratorPvHybridModeOpen",
        icon_on="mdi:solar-power",
        icon_off="mdi:solar-power-variant-outline",
    ),
    EcoFlowSwitchDef(
        key="generator_care_mode",
        name="Generator Care Mode",
        state_key="generatorCareModeOpen",
        param_key="cfgGeneratorCareModeOpen",
        icon_on="mdi:heart",
        icon_off="mdi:heart-outline",
    ),
]
