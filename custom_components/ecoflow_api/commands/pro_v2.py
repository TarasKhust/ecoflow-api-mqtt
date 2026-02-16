"""ProV2 command format for Delta Pro 3 and Stream Ultra X."""

from __future__ import annotations

from ..const import JsonVal


class ProV2CommandBuilder:
    """Builds payloads in cmdId/cmdFunc format.

    Used by: Delta Pro 3, Stream Ultra X.
    REST: {sn, cmdId:17, cmdFunc:254, dirDest:1, dirSrc:1, dest:2, needAck:true, params}
    MQTT: same + id/version auto-injected by mqtt_client.
    """

    def build_command(
        self,
        device_sn: str,
        params: dict[str, JsonVal],
        **kwargs: int | str,
    ) -> dict[str, JsonVal]:
        return {
            "sn": device_sn,
            "cmdId": 17,
            "cmdFunc": 254,
            "dirDest": 1,
            "dirSrc": 1,
            "dest": 2,
            "needAck": True,
            "params": params,
        }
