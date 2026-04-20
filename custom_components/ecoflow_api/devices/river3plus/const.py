"""Constants for River 3 Plus device."""
from __future__ import annotations

from typing import Final

# Device information
DEVICE_TYPE: Final = "River 3 Plus"
DEVICE_MODEL: Final = "River 3 Plus"

# Supported MQTT + Protobuf sensor keys
SENSOR_KEYS: Final[tuple[str, ...]] = (
    "battery_level",
    "temperature",
    "ac_in_power",
    "pow_in_sum_w",
    "pow_out_sum_w",
    "temp_pcs_dc",
    "temp_pcs_ac",
    "ac_in_voltage",
    "ac_out_voltage",
    "ac_in_current",
    "ac_out_current",
)
