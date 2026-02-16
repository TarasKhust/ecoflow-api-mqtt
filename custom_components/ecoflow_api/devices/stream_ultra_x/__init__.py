"""Stream Ultra X device profile."""

from ...commands.base import CommandFormat
from ..base import DeviceProfile
from .binary_sensors import BINARY_SENSORS
from .buttons import BUTTONS
from .numbers import NUMBERS
from .selects import SELECTS
from .sensors import SENSORS
from .switches import SWITCHES

PROFILE = DeviceProfile(
    device_type="stream_ultra_x",
    display_name="Stream Ultra X",
    command_format=CommandFormat.PRO_V2,
    sensors=SENSORS,
    switches=SWITCHES,
    numbers=NUMBERS,
    selects=SELECTS,
    binary_sensors=BINARY_SENSORS,
    buttons=BUTTONS,
)
