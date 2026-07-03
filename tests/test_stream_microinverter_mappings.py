"""Regression coverage for Stream Microinverter device mappings."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_COMPONENT = ROOT / "custom_components" / "ecoflow_api"
DEVICE_TYPE = "DEVICE_TYPE_STREAM_MICRO_INVERTER"


def _source(path: str) -> str:
    return (CUSTOM_COMPONENT / path).read_text(encoding="utf-8")


class StreamMicroinverterMappingTest(unittest.TestCase):
    def test_stream_microinverter_is_available_in_device_types(self) -> None:
        source = _source("const.py")
        tree = ast.parse(source)
        assignments = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assignments.update(
                    {
                        target.id: node.value
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    }
                )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                assignments[node.target.id] = node.value

        self.assertIn(DEVICE_TYPE, assignments)

        device_types = assignments["DEVICE_TYPES"]
        self.assertIsInstance(device_types, ast.Dict)
        keys = {ast.unparse(key) for key in device_types.keys}
        values = {ast.literal_eval(value) for value in device_types.values}

        self.assertIn(DEVICE_TYPE, keys)
        self.assertIn("Stream Microinverter", values)

    def test_stream_microinverter_platform_maps_are_registered(self) -> None:
        expected_maps = {
            "sensor.py": "DEVICE_SENSOR_MAP",
            "binary_sensor.py": "DEVICE_BINARY_SENSOR_MAP",
            "number.py": "DEVICE_NUMBER_MAP",
            "switch.py": "DEVICE_SWITCH_MAP",
            "select.py": "DEVICE_SELECT_MAP",
            "button.py": "DEVICE_BUTTON_MAP",
        }

        for filename, map_name in expected_maps.items():
            with self.subTest(filename=filename):
                source = _source(filename)
                self.assertIn(DEVICE_TYPE, source)
                self.assertIn(map_name, source)


class BkwMainSnRoutingTest(unittest.TestCase):
    def test_api_exposes_main_sn_endpoint(self) -> None:
        source = _source("api.py")
        self.assertIn("async def get_main_device_sn", source)
        self.assertIn("/iot-open/sign/device/system/main/sn", source)

    def test_coordinator_defaults_command_sn_to_device_sn(self) -> None:
        source = _source("coordinator.py")
        self.assertIn("self.command_sn = command_sn or device_sn", source)
        self.assertIn("device_sn=self.command_sn", source)
        self.assertIn("command[\"sn\"] = self.command_sn", source)

    def test_mqtt_command_topics_use_command_sn(self) -> None:
        source = _source("mqtt_client.py")
        self.assertIn("self.command_sn = command_sn or device_sn", source)
        self.assertIn(
            "self._set_topic = f\"/open/{self._certificate_account}/{self.command_sn}/set\"",
            source,
        )
        self.assertIn(
            "self._set_reply_topic = f\"/open/{self._certificate_account}/{self.command_sn}/set_reply\"",
            source,
        )
        self.assertIn(
            "self._quota_topic = f\"/open/{self._certificate_account}/{device_sn}/quota\"",
            source,
        )

    def test_setup_resolves_main_sn_for_stream_devices(self) -> None:
        source = _source("__init__.py")
        self.assertIn("get_main_device_sn", source)
        self.assertIn("DEVICE_TYPE_STREAM_ULTRA_X", source)
        self.assertIn("DEVICE_TYPE_STREAM_ULTRA", source)
        self.assertIn("command_sn = configured_sn", source)


if __name__ == "__main__":
    unittest.main()
