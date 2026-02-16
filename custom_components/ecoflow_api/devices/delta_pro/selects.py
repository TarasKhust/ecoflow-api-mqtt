"""Select definitions for EcoFlow Delta Pro."""

from __future__ import annotations

from ..base import EcoFlowSelectDef

SELECTS: list[EcoFlowSelectDef] = [
    EcoFlowSelectDef(
        key="pv_charging_type",
        name="PV Charging Type",
        param_key="chgType",
        state_key="mppt.cfgChgType",
        command_params={"cmd_set": 32, "cmd_id": 82},
        icon="mdi:solar-power",
        options={"Auto": 0, "MPPT": 1, "Adapter": 2},
    ),
    EcoFlowSelectDef(
        key="ac_output_frequency",
        name="AC Output Frequency",
        param_key="cfgAcOutFreq",
        state_key="inv.cfgAcOutFreq",
        command_params={"cmd_set": 32, "cmd_id": 66},
        icon="mdi:sine-wave",
        options={"50 Hz": 1, "60 Hz": 2},
    ),
]
