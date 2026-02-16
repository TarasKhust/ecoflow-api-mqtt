"""Device registry for EcoFlow API integration.

Auto-discovers device profiles from subdirectories. Each device module
must expose a PROFILE attribute of type DeviceProfile.

Usage:
    from .devices import get_profile, get_device_types

    profile = get_profile("delta_pro_3")
    device_types = get_device_types()  # {"delta_pro_3": "Delta Pro 3", ...}
"""

from __future__ import annotations

from .base import DeviceProfile
from .delta_2 import PROFILE as _DELTA_2
from .delta_pro import PROFILE as _DELTA_PRO
from .delta_pro_3 import PROFILE as _DELTA_PRO_3
from .smart_plug import PROFILE as _SMART_PLUG
from .stream_ultra_x import PROFILE as _STREAM_ULTRA_X

_PROFILES: dict[str, DeviceProfile] = {
    p.device_type: p
    for p in (
        _DELTA_PRO_3,
        _DELTA_PRO,
        _DELTA_2,
        _STREAM_ULTRA_X,
        _SMART_PLUG,
    )
}


def get_profile(device_type: str) -> DeviceProfile | None:
    """Get device profile by device type string."""
    return _PROFILES.get(device_type)


def get_device_types() -> dict[str, str]:
    """Return mapping of device_type -> display_name for config flow."""
    return {p.device_type: p.display_name for p in _PROFILES.values()}


def get_all_profiles() -> dict[str, DeviceProfile]:
    """Return all registered device profiles."""
    return dict(_PROFILES)
