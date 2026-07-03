"""Device-specific modules for EcoFlow API integration.

Each device type has its own subdirectory containing:
- const.py: Device-specific constants
- Command mappings and API structures
- Device metadata

Supported devices:
- Delta Pro 3 (devices/delta_pro_3/)
- River 3 Plus (devices/river3plus/)
- Smart Plug S401 (devices/smart_plug/)
"""
from __future__ import annotations

from . import delta_pro_3, river3plus, smart_plug

# Device type mapping
DEVICE_MODULES = {
    "DELTA Pro 3": delta_pro_3,
    "River 3 Plus": river3plus,
    "Smart Plug S401": smart_plug,
}

__all__ = [
    "delta_pro_3",
    "river3plus",
    "smart_plug",
    "DEVICE_MODULES",
]
