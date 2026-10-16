"""Focused coverage for PowerStream inverter_output_power (deciwatts -> W).

Exercises the real definition from POWERSTREAM_MICRO_INVERTER_SENSOR_DEFINITIONS
through the real EcoFlowSensor.native_value lookup (flat + nested quota data).
No hardware or network.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower

from custom_components.ecoflow_api.sensor import (
    EcoFlowSensor,
    POWERSTREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
)

DEFINITION = POWERSTREAM_MICRO_INVERTER_SENSOR_DEFINITIONS["inverter_output_power"]

# (label, coordinator data, expected native_value)
CASES: list[tuple[str, dict | None, float | None]] = [
    ("flat integer deciwatts", {"20_1.invOutputWatts": 4567}, 456.7),
    ("flat small fractional", {"20_1.invOutputWatts": 5}, 0.5),
    ("flat exact ten", {"20_1.invOutputWatts": 10}, 1.0),
    ("flat zero stays zero", {"20_1.invOutputWatts": 0}, 0.0),
    ("nested fallback", {"20_1": {"invOutputWatts": 1234}}, 123.4),
    ("nested zero stays zero", {"20_1": {"invOutputWatts": 0}}, 0.0),
    ("explicit None", {"20_1.invOutputWatts": None}, None),
    ("missing field", {"20_1.batSoc": 80}, None),
    ("empty data", {}, None),
    ("no data None", None, None),
]


def _sensor_with_data(data: dict | None) -> EcoFlowSensor:
    sensor = object.__new__(EcoFlowSensor)
    sensor.coordinator = SimpleNamespace(data=data)
    sensor._sensor_config = DEFINITION
    sensor._attr_device_class = DEFINITION.get("device_class")
    return sensor


class InverterOutputPowerTest(unittest.TestCase):
    def test_definition_metadata(self) -> None:
        self.assertEqual(DEFINITION["key"], "20_1.invOutputWatts")
        self.assertEqual(DEFINITION["unit"], UnitOfPower.WATT)
        self.assertEqual(DEFINITION["device_class"], SensorDeviceClass.POWER)
        self.assertEqual(DEFINITION["state_class"], SensorStateClass.MEASUREMENT)
        self.assertTrue(callable(DEFINITION["value_map"]))

    def test_native_value_routing_and_conversion(self) -> None:
        for label, data, expected in CASES:
            with self.subTest(label=label):
                sensor = _sensor_with_data(data)
                result = sensor.native_value
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertAlmostEqual(result, expected, places=6)

    def test_runtime_value_changes_same_instance(self) -> None:
        sensor = _sensor_with_data({"20_1.invOutputWatts": 1000})
        self.assertAlmostEqual(sensor.native_value, 100.0, places=6)
        sensor.coordinator.data = {"20_1.invOutputWatts": 2505}
        self.assertAlmostEqual(sensor.native_value, 250.5, places=6)
        sensor.coordinator.data = {"20_1": {"invOutputWatts": 42}}
        self.assertAlmostEqual(sensor.native_value, 4.2, places=6)
        sensor.coordinator.data = {}
        self.assertIsNone(sensor.native_value)


if __name__ == "__main__":
    unittest.main()
