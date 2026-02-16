"""Stream Ultra X button definitions."""

from __future__ import annotations

from ..base import EcoFlowButtonDef

BUTTONS = [
    EcoFlowButtonDef(
        key="power_off",
        name="Power Off",
        param_key="cfgPowerOff",
        icon="mdi:power",
    ),
]
