"""Constants for EcoFlow Smart Plug S401."""
from __future__ import annotations

from typing import Final

# Device identification
DEVICE_TYPE: Final = "SMART_PLUG"
DEVICE_MODEL: Final = "Smart Plug S401"

# Smart Plug uses a different command structure than Delta Pro 3
# Commands use cmdCode instead of cmdId/cmdFunc
# Format: {"sn": "DEVICE_SN", "cmdCode": "COMMAND_CODE", "params": {...}}
COMMAND_BASE: Final[dict[str, int | str | bool]] = {
    # Smart Plug doesn't use the same command base structure as Delta Pro 3
    # Commands are sent with cmdCode directly
}

# Command codes for Smart Plug
CMD_CODE_SWITCH: Final = "WN511_SOCKET_SET_PLUG_SWITCH_MESSAGE"
CMD_CODE_BRIGHTNESS: Final = "WN511_SOCKET_SET_BRIGHTNESS_PACK"
CMD_CODE_MAX_WATTS: Final = "WN511_SOCKET_SET_MAX_WATTS"  # Overload protection threshold
CMD_CODE_DELETE_TASK: Final = "WN511_SOCKET_DELETE_TIME_TASK"
