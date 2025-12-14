"""Constants for Delta Pro 3."""
from __future__ import annotations

from typing import Final

# Device information
DEVICE_TYPE: Final = "DELTA Pro 3"
DEVICE_MODEL: Final = "Delta Pro 3"

# API Command structure - all Delta Pro 3 commands use this base
COMMAND_BASE: Final = {
    "cmdId": 17,
    "dirDest": 1,
    "dirSrc": 1,
    "cmdFunc": 254,
    "dest": 2,
    "needAck": True,
}


