"""Stream Ultra X number definitions."""

from __future__ import annotations

from homeassistant.components.number import NumberMode
from homeassistant.const import PERCENTAGE

from ..base import EcoFlowNumberDef

NUMBERS = [
    EcoFlowNumberDef(
        key="backup_reserve_level",
        name="Backup Reserve Level",
        state_key="backupReverseSoc",
        param_key="cfgBackupReverseSoc",
        min_value=3,
        max_value=95,
        step=1,
        unit=PERCENTAGE,
        icon="mdi:battery-heart",
        mode=NumberMode.SLIDER,
    ),
    EcoFlowNumberDef(
        key="max_charge_level",
        name="Max Charge Level",
        state_key="cmsMaxChgSoc",
        param_key="cfgMaxChgSoc",
        min_value=50,
        max_value=100,
        step=1,
        unit=PERCENTAGE,
        icon="mdi:battery-charging-100",
        mode=NumberMode.SLIDER,
    ),
    EcoFlowNumberDef(
        key="min_discharge_level",
        name="Min Discharge Level",
        state_key="cmsMinDsgSoc",
        param_key="cfgMinDsgSoc",
        min_value=0,
        max_value=30,
        step=1,
        unit=PERCENTAGE,
        icon="mdi:battery-low",
        mode=NumberMode.SLIDER,
    ),
]
