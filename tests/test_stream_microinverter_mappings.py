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


if __name__ == "__main__":
    unittest.main()
