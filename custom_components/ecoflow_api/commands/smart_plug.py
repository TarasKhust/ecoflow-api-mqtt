"""Smart Plug command format for EcoFlow Smart Plug S401."""

from __future__ import annotations

from ..const import JsonVal


class SmartPlugCommandBuilder:
    """Builds payloads in cmdCode format.

    Used by: Smart Plug S401.
    REST: {sn, cmdCode:"WN511_...", params}
    MQTT: same + id/version auto-injected by mqtt_client.
    """

    def build_command(
        self,
        device_sn: str,
        params: dict[str, JsonVal],
        **kwargs: int | str,
    ) -> dict[str, JsonVal]:
        cmd_code = str(kwargs["cmd_code"])
        return {
            "sn": device_sn,
            "cmdCode": cmd_code,
            "params": params,
        }
