"""Abstract command builder protocol and command format enum."""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol


class CommandFormat(str, Enum):
    """Supported device command formats."""

    PRO_V2 = "pro_v2"  # Delta Pro 3, Stream Ultra X
    PRO_V1 = "pro_v1"  # Delta Pro (original)
    DELTA_V2 = "delta_v2"  # Delta 2
    SMART_PLUG = "smart_plug"  # Smart Plug S401


class CommandBuilder(Protocol):
    """Protocol for building device command payloads."""

    def build_command(
        self,
        device_sn: str,
        params: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build a command payload for the device.

        Args:
            device_sn: Device serial number.
            params: Command parameters (e.g., {"cfgAcOutOpen": True}).
            **kwargs: Format-specific args (cmd_set, cmd_id, module_type,
                      operate_type, cmd_code, etc.).

        Returns:
            Complete command payload ready to send via coordinator.
        """
        ...
