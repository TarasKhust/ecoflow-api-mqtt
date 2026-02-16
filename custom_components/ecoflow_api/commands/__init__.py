"""Command builder factory for EcoFlow device command payloads."""

from __future__ import annotations

from ..const import JsonVal
from .base import CommandBuilder, CommandFormat
from .delta_v2 import DeltaV2CommandBuilder
from .pro_v1 import ProV1CommandBuilder
from .pro_v2 import ProV2CommandBuilder
from .smart_plug import SmartPlugCommandBuilder

__all__ = ["CommandBuilder", "CommandFormat", "build_command", "get_command_builder"]

_BUILDERS: dict[CommandFormat, CommandBuilder] = {
    CommandFormat.PRO_V2: ProV2CommandBuilder(),
    CommandFormat.PRO_V1: ProV1CommandBuilder(),
    CommandFormat.DELTA_V2: DeltaV2CommandBuilder(),
    CommandFormat.SMART_PLUG: SmartPlugCommandBuilder(),
}


def get_command_builder(fmt: CommandFormat) -> CommandBuilder:
    """Get command builder instance for a given format."""
    return _BUILDERS[fmt]


def build_command(
    fmt: CommandFormat,
    device_sn: str,
    params: dict[str, JsonVal],
    **kwargs: int | str,
) -> dict[str, JsonVal]:
    """Build a command payload using the appropriate format builder.

    Args:
        fmt: Command format to use.
        device_sn: Device serial number.
        params: Command parameters dict.
        **kwargs: Format-specific arguments (cmd_set, cmd_id, module_type, etc.).

    Returns:
        Complete command payload ready to send.
    """
    return _BUILDERS[fmt].build_command(device_sn, params, **kwargs)
