"""DeltaV2 command format for Delta 2."""

from __future__ import annotations

import time

from ..const import JsonVal


class DeltaV2CommandBuilder:
    """Builds payloads in moduleType/operateType format.

    Used by: Delta 2.
    REST: {id, version:"1.0", sn, moduleType, operateType, params}
    MQTT: same format (id/version already present, mqtt_client won't add duplicates).
    """

    def build_command(
        self,
        device_sn: str,
        params: dict[str, JsonVal],
        **kwargs: int | str,
    ) -> dict[str, JsonVal]:
        module_type = int(kwargs["module_type"])
        operate_type = str(kwargs["operate_type"])
        return {
            "id": int(time.time() * 1000),
            "version": "1.0",
            "sn": device_sn,
            "moduleType": module_type,
            "operateType": operate_type,
            "params": params,
        }
