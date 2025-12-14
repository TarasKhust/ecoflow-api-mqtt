"""Device-specific modules for EcoFlow API integration.

Each device type has its own subdirectory containing:
- const.py: Device-specific constants
- Command mappings and API structures
- Device metadata

Supported devices:
- Delta Pro 3 (devices/delta_pro_3/)
"""
from __future__ import annotations

from . import delta_pro_3

# Device type mapping
DEVICE_MODULES = {
    "DELTA Pro 3": delta_pro_3,
}

__all__ = [
    "delta_pro_3",
    "DEVICE_MODULES",
]

