"""River 3 Plus device wrapper."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import DEVICE_MODEL, DEVICE_TYPE, SENSOR_KEYS
from .proto_decoder import River3PlusProtoDecoder


@dataclass(slots=True)
class River3PlusDevice:
    """Device-local River 3 Plus helpers for MQTT protobuf telemetry."""

    device_sn: str
    decoder: River3PlusProtoDecoder = field(init=False)
    device_type: str = field(init=False, default=DEVICE_TYPE)
    model: str = field(init=False, default=DEVICE_MODEL)
    sensor_keys: tuple[str, ...] = field(init=False, default=SENSOR_KEYS)

    def __post_init__(self) -> None:
        """Create the protobuf decoder for this device instance."""
        self.decoder = River3PlusProtoDecoder(self.device_sn)

    def decode_packet(self, payload: bytes) -> dict[str, Any] | None:
        """Decode a raw MQTT protobuf payload into sensor updates."""
        return self.decoder.decode(payload)
