"""Delta 2 select definitions."""

from __future__ import annotations

from ..base import EcoFlowSelectDef

SELECTS = [
    EcoFlowSelectDef(
        key="ac_output_frequency",
        name="AC Output Frequency",
        param_key="out_freq",
        state_key="inv.cfgAcOutFreq",
        command_params={"module_type": 5, "operate_type": "acOutCfg"},
        icon="mdi:sine-wave",
        options={"50 Hz": 1, "60 Hz": 2},
    ),
    EcoFlowSelectDef(
        key="solar_priority",
        name="Solar Charging Priority",
        param_key="pvChangeSet",
        state_key="pd.pvChgPrioSet",
        command_params={"module_type": 1, "operate_type": "pvChangePrio"},
        icon="mdi:solar-power",
        options={"Off": 0, "On": 1},
    ),
]
