"""Constants for Delta Pro Ultra."""
from __future__ import annotations

from typing import Final

DEVICE_TYPE: Final = "DELTA Pro Ultra"
DEVICE_MODEL: Final = "Delta Pro Ultra"

# Delta Pro Ultra uses cmdCode-based commands (YJ751 format)
# HTTP: PUT /iot-open/sign/device/quota with cmdCode in payload
# MQTT: publish to /open/${certificateAccount}/${sn}/set with cmdCode
CMD_AC_DSG_SET: Final = "YJ751_PD_AC_DSG_SET"
CMD_DC_SWITCH_SET: Final = "YJ751_PD_DC_SWITCH_SET"
CMD_BP_HEAT_SET: Final = "YJ751_PD_BP_HEAT_SET"
CMD_POWER_STANDBY_SET: Final = "YJ751_PD_POWER_STANDBY_SET"
CMD_SCREEN_STANDBY_SET: Final = "YJ751_PD_SCREEN_STANDBY_SET"
CMD_AC_STANDBY_SET: Final = "YJ751_PD_AC_STANDBY_SET"
CMD_DC_STANDBY_SET: Final = "YJ751_PD_DC_STANDBY_SET"
CMD_CHG_SOC_MAX_SET: Final = "YJ751_PD_CHG_SOC_MAX_SET"
CMD_DSG_SOC_MIN_SET: Final = "YJ751_PD_DSG_SOC_MIN_SET"
CMD_4G_SWITCH_SET: Final = "YJ751_PD_4G_SWITCH_SET"
CMD_AC_OFTEN_OPEN_SET: Final = "YJ751_PD_AC_OFTEN_OPEN_SET"
CMD_AC_CHG_SET: Final = "YJ751_PD_AC_CHG_SET"
