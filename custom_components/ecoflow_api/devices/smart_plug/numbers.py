"""Number definitions for EcoFlow Smart Plug S401."""

from __future__ import annotations

from homeassistant.components.number import NumberMode
from homeassistant.const import PERCENTAGE

from ..base import EcoFlowNumberDef

NUMBERS: list[EcoFlowNumberDef] = [
    EcoFlowNumberDef(
        key="led_brightness",
        name="LED Brightness",
        state_key="2_1.brightness",
        param_key="brightness",
        command_params={"cmd_code": "WN511_SOCKET_SET_BRIGHTNESS_PACK"},
        min_value=0,
        max_value=100,
        step=1,
        unit=PERCENTAGE,
        icon="mdi:brightness-6",
        mode=NumberMode.SLIDER,
        value_to_ui=lambda x: round((x / 1023) * 100) if x is not None else None,
        value_from_ui=lambda x: round((x / 100) * 1023) if x is not None else None,
    ),
]
