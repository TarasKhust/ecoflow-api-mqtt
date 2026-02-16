"""ProV1 command format for Delta Pro (original)."""

from __future__ import annotations

from typing import Any


class ProV1CommandBuilder:
    """Builds payloads in cmdSet/id format.

    Used by: Delta Pro (original).
    REST: {sn, params: {cmdSet, id, ...value}}
    MQTT: same + id/version/operateType/timestamp auto-injected by mqtt_client.
    """

    def build_command(
        self,
        device_sn: str,
        params: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        cmd_set: int = kwargs["cmd_set"]
        cmd_id: int = kwargs["cmd_id"]
        return {
            "sn": device_sn,
            "params": {
                "cmdSet": cmd_set,
                "id": cmd_id,
                **params,
            },
        }
