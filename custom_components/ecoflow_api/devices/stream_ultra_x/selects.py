"""Stream Ultra X select definitions."""

from __future__ import annotations

from ..base import EcoFlowSelectDef

SELECTS = [
    EcoFlowSelectDef(
        key="operating_mode",
        name="Operating Mode",
        param_key="cfgEnergyStrategyOperateMode",
        state_key="energyStrategyOperateMode",
        icon="mdi:cog",
        options={
            "Self-Powered": {"operateSelfPoweredOpen": True},
            "AI Mode": {"operateIntelligentScheduleModeOpen": True},
        },
        nested_params=True,
    ),
]
