"""Regression coverage for Stream base-load (issue #49) mapping."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NUMBER_PATH = ROOT / "custom_components" / "ecoflow_api" / "number.py"


class StreamBaseLoadMappingTest(unittest.TestCase):
    def test_base_load_number_uses_resident_load_schedule(self) -> None:
        source = NUMBER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = {
            target.id: node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

        stream_numbers = assignments["STREAM_ULTRA_X_NUMBER_DEFINITIONS"]
        self.assertIsInstance(stream_numbers, ast.Dict)

        for key, value in zip(stream_numbers.keys, stream_numbers.values):
            if ast.literal_eval(key) == "base_load_power":
                self.assertIsInstance(value, ast.Dict)
                number_config = {
                    ast.literal_eval(config_key): config_value
                    for config_key, config_value in zip(value.keys, value.values)
                    if isinstance(config_key, ast.Constant)
                }
                break
        else:
            self.fail("base_load_power is missing")

        self.assertEqual(
            ast.literal_eval(number_config["state_key"]), "dayResidentLoadList"
        )
        self.assertEqual(
            ast.literal_eval(number_config["param_key"]), "cfgDayResidentLoadList"
        )
        self.assertTrue(ast.literal_eval(number_config["resident_load_schedule"]))
        # Stable entity must not carry the alpha experimental flag.
        self.assertNotIn("experimental", number_config)

    def test_stream_number_native_value_reads_resident_schedule(self) -> None:
        """EcoFlowStreamNumber.native_value must decode the schedule, not float() it.

        Regression for the "unknown" state in the entity pop-out/dashboard: the
        read path used float(dayResidentLoadList_dict) -> None. It must route
        resident_load_schedule entities through _extract_resident_load_power, the
        same way EcoFlowNumber.native_value does.
        """
        source = NUMBER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        stream_cls = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "EcoFlowStreamNumber"
        )
        native_value = next(
            node
            for node in stream_cls.body
            if isinstance(node, ast.FunctionDef) and node.name == "native_value"
        )
        segment = ast.get_source_segment(source, native_value) or ""
        self.assertIn("resident_load_schedule", segment)
        self.assertIn("_extract_resident_load_power", segment)


if __name__ == "__main__":
    unittest.main()
