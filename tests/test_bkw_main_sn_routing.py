"""Regression coverage for multi-device BKW main-SN command routing (issue #48).

These are lightweight source-level checks (no Home Assistant import needed) that
guard the two-SN routing wiring: commands must target the resolved main device
SN, while state is still read from the configured device SN.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "ecoflow_api"


class BkwMainSnRoutingTest(unittest.TestCase):
    def test_api_exposes_main_sn_endpoint(self) -> None:
        api = (PKG / "api.py").read_text(encoding="utf-8")
        self.assertIn("async def get_main_device_sn", api)
        self.assertIn("/iot-open/sign/device/system/main/sn", api)

    def test_coordinator_defaults_command_sn_to_device_sn(self) -> None:
        coord = (PKG / "coordinator.py").read_text(encoding="utf-8")
        self.assertIn("self.command_sn = command_sn or device_sn", coord)
        # Commands route to command_sn, not device_sn.
        self.assertIn("device_sn=self.command_sn", coord)

    def test_mqtt_command_topics_use_command_sn(self) -> None:
        mqtt = (PKG / "mqtt_client.py").read_text(encoding="utf-8")
        self.assertIn("self.command_sn = command_sn or device_sn", mqtt)
        self.assertIn(
            "self._set_topic = f\"/open/{self._certificate_account}/{self.command_sn}/set\"",
            mqtt,
        )
        self.assertIn(
            "self._set_reply_topic = f\"/open/{self._certificate_account}/{self.command_sn}/set_reply\"",
            mqtt,
        )
        # State topics stay on device_sn.
        self.assertIn(
            "self._quota_topic = f\"/open/{self._certificate_account}/{device_sn}/quota\"",
            mqtt,
        )

    def test_setup_resolves_main_sn_for_stream_only(self) -> None:
        init = (PKG / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("get_main_device_sn", init)
        self.assertIn("DEVICE_TYPE_STREAM_ULTRA_X", init)
        # Falls back to the configured SN (assigned before the conditional).
        self.assertIn("command_sn = configured_sn", init)


if __name__ == "__main__":
    unittest.main()
