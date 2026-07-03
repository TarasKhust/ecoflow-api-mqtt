"""Regression coverage for Stream base-load (issue #49) mapping."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NUMBER_PATH = ROOT / "custom_components" / "ecoflow_api" / "number.py"
SERVICES_PATH = ROOT / "custom_components" / "ecoflow_api" / "services.py"


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

    def test_base_load_schedule_service_uses_confirmed_command(self) -> None:
        """The schedule service must write cfgDayResidentLoadList with load periods."""
        source = SERVICES_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        constants = {
            target.id: node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

        self.assertEqual(
            ast.literal_eval(constants["SERVICE_SET_BASE_LOAD_SCHEDULE"]),
            "set_base_load_schedule",
        )
        self.assertEqual(
            ast.literal_eval(constants["STREAM_BASE_LOAD_PARAM_KEY"]),
            "cfgDayResidentLoadList",
        )
        self.assertEqual(
            ast.literal_eval(constants["STREAM_BASE_LOAD_STATE_KEY"]),
            "dayResidentLoadList",
        )

        command_func = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_stream_base_load_command"
        )
        segment = ast.get_source_segment(source, command_func) or ""
        self.assertIn('"cmdId": 17', segment)
        self.assertIn('"cmdFunc": 254', segment)
        self.assertIn('"needAck": True', segment)
        self.assertIn("STREAM_BASE_LOAD_PARAM_KEY", segment)

    def test_base_load_schedule_service_translates_period_keys(self) -> None:
        """Service data uses HA-friendly keys and sends EcoFlow's API keys."""
        source = SERVICES_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        payload_func = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_stream_base_load_payload"
        )
        segment = ast.get_source_segment(source, payload_func) or ""

        self.assertIn('"startMin"', segment)
        self.assertIn('"endMin"', segment)
        self.assertIn('"loadPower"', segment)
        self.assertIn("ATTR_START_MIN", segment)
        self.assertIn("ATTR_END_MIN", segment)
        self.assertIn("ATTR_LOAD_POWER", segment)


if __name__ == "__main__":
    unittest.main()
