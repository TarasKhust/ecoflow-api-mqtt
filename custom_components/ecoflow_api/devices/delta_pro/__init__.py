"""Delta Pro (original) device profile."""

from ...commands.base import CommandFormat
from ..base import DeviceProfile
from .binary_sensors import BINARY_SENSORS
from .numbers import NUMBERS
from .selects import SELECTS
from .sensors import SENSORS
from .switches import SWITCHES

PROFILE = DeviceProfile(
    device_type="delta_pro",
    display_name="Delta Pro",
    command_format=CommandFormat.PRO_V1,
    sensors=SENSORS,
    switches=SWITCHES,
    numbers=NUMBERS,
    selects=SELECTS,
    binary_sensors=BINARY_SENSORS,
)
