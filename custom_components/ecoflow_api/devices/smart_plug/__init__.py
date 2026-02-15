"""Smart Plug S401 device-specific module."""
from __future__ import annotations

from .const import (
    CMD_CODE_BRIGHTNESS,
    CMD_CODE_DELETE_TASK,
    CMD_CODE_SWITCH,
    COMMAND_BASE,
    DEVICE_MODEL,
    DEVICE_TYPE,
)

__all__ = [
    "DEVICE_TYPE",
    "DEVICE_MODEL",
    "COMMAND_BASE",
    "CMD_CODE_SWITCH",
    "CMD_CODE_BRIGHTNESS",
    "CMD_CODE_DELETE_TASK",
]
