"""Delta 2 / Delta 2 Max ENUM sensors must not break on values seen on real units."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.ecoflow_api.sensor import (
    DELTA_2_MAX_SENSOR_DEFINITIONS,
    EcoFlowSensor,
)


def _value(sensor_id: str, data: dict[str, Any]) -> Any:
    config = DELTA_2_MAX_SENSOR_DEFINITIONS[sensor_id]
    sensor = object.__new__(EcoFlowSensor)
    sensor.coordinator = SimpleNamespace(data=data)
    sensor._sensor_id = sensor_id
    sensor._sensor_config = config
    sensor._attr_device_class = config["device_class"]
    value = sensor.native_value
    assert value is None or value in config["options"]
    return value


@pytest.mark.parametrize(
    ("raw", "expected"), [(0, "unplugged"), (1, "plugged"), (34, "plugged")]
)
def test_charge_line_plugged_treats_non_zero_as_plugged(raw: int, expected: str) -> None:
    assert _value("ems_chg_line_plug", {"bms_emsStatus.chgLinePlug": raw}) == expected


@pytest.mark.parametrize(("raw", "expected"), [(1, "ac"), (255, "idle")])
def test_inverter_charger_type_idle(raw: int, expected: str) -> None:
    assert _value("inv_charger_type", {"inv.chargerType": raw}) == expected


@pytest.mark.parametrize(
    ("raw", "expected"), [(0, "not_charging"), (1, "charging"), (2, "charging"), (3, "ups"), (4, "error")]
)
def test_ems_charge_state(raw: int, expected: str) -> None:
    assert _value("ems_chg_state", {"bms_emsStatus.chgState": raw}) == expected


@pytest.mark.parametrize(("raw", "expected"), [(0, "not_charging"), (2, "charging")])
def test_battery_charge_state_cv_is_charging(raw: int, expected: str) -> None:
    assert _value("bms_chg_state", {"bms_bmsStatus.chgState": raw}) == expected


@pytest.mark.parametrize(("raw", "expected"), [(1, "mppt"), (3, "unknown")])
def test_xt60_charge_type_unknown_value(raw: int, expected: str) -> None:
    assert _value("mppt_x60_chg_type", {"mppt.x60ChgType": raw}) == expected
