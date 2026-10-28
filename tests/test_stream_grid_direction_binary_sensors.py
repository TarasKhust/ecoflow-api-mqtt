"""Regression tests for Stream grid direction binary sensors (issue #88).

Grid Connection Power on Stream devices is positive while exporting to the
grid and negative while importing.  The binary sensors must follow that sign.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.ecoflow_api.binary_sensor import (
    DEVICE_BINARY_SENSOR_MAP,
    EcoFlowBinarySensor,
    POWERSTREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS,
    STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS,
    STREAM_ULTRA_X_BINARY_SENSOR_DEFINITIONS,
)
from custom_components.ecoflow_api.const import (
    DEVICE_TYPE_STREAM_AC_PRO,
    DEVICE_TYPE_STREAM_MICRO_INVERTER,
    DEVICE_TYPE_STREAM_ULTRA_X,
)
from custom_components.ecoflow_api.sensor import (
    EcoFlowSensor,
    STREAM_AC_PRO_SENSOR_DEFINITIONS,
    STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS,
    STREAM_ULTRA_X_SENSOR_DEFINITIONS,
)
from homeassistant.const import UnitOfPower


MODEL_ROUTES = (
    DEVICE_TYPE_STREAM_ULTRA_X,
    "stream_ultra",
    DEVICE_TYPE_STREAM_AC_PRO,
)

# value, is grid_feed_in on, is grid_consuming on
GRID_CASES = (
    (1697, True, False),
    (-1697, False, True),
    (200, True, False),
    (-200, False, True),
    (-2246, False, True),
    (0, False, False),
    (-10, False, False),
    (10, False, False),
    (10.0001, True, False),
    (-10.0001, False, True),
    (10.5, True, False),
    (-10.5, False, True),
)


def _coordinator(data, device_type=DEVICE_TYPE_STREAM_ULTRA_X):
    return SimpleNamespace(
        data=data,
        last_update_success=True,
        device_sn="TEST-SN",
        device_type=device_type,
    )


def _sensor(key, data, definitions=STREAM_ULTRA_X_BINARY_SENSOR_DEFINITIONS,
            device_type=DEVICE_TYPE_STREAM_ULTRA_X):
    return EcoFlowBinarySensor(
        coordinator=_coordinator(data, device_type),
        sensor_key=key,
        sensor_def=definitions[key],
    )


def _grid_power(value):
    return {"gridConnectionPower": value}


@pytest.mark.parametrize("value,feed_in,consuming", GRID_CASES)
def test_grid_direction_sensors_follow_positive_export_sign(value, feed_in, consuming):
    assert _sensor("grid_feed_in", _grid_power(value)).is_on is feed_in
    assert _sensor("grid_consuming", _grid_power(value)).is_on is consuming


@pytest.mark.parametrize("key", ["grid_feed_in", "grid_consuming"])
def test_missing_grid_power_value_keeps_existing_off_behaviour(key):
    # Derived sensor: a present-but-None field evaluates False (unchanged).
    assert _sensor(key, _grid_power(None)).is_on is False


@pytest.mark.parametrize("key", ["grid_feed_in", "grid_consuming"])
def test_missing_field_and_missing_data_keep_existing_behaviour(key):
    # Missing field evaluates False; absent coordinator data is unknown.
    assert _sensor(key, {"powGetSysGrid": 500}).is_on is False
    assert _sensor(key, {}).is_on is None
    assert _sensor(key, None).is_on is None


@pytest.mark.parametrize("route", MODEL_ROUTES)
def test_ultra_ultra_x_and_ac_pro_routes_share_corrected_direction(route):
    definitions = DEVICE_BINARY_SENSOR_MAP[route]
    assert definitions is STREAM_ULTRA_X_BINARY_SENSOR_DEFINITIONS

    exporting = _sensor("grid_feed_in", _grid_power(1697), definitions, route)
    importing = _sensor("grid_consuming", _grid_power(-1697), definitions, route)
    idle = _sensor("grid_feed_in", _grid_power(0), definitions, route)

    assert exporting.is_on is True
    assert importing.is_on is True
    assert idle.is_on is False


@pytest.mark.parametrize(
    "key,name,icon_on,icon_off",
    (
        ("grid_feed_in", "Grid Feed-in", "mdi:transmission-tower-export",
         "mdi:transmission-tower"),
        ("grid_consuming", "Grid Consuming", "mdi:transmission-tower-import",
         "mdi:transmission-tower"),
    ),
)
def test_grid_sensor_identity_and_icons_preserved(key, name, icon_on, icon_off):
    definition = STREAM_ULTRA_X_BINARY_SENSOR_DEFINITIONS[key]
    assert definition["name"] == name
    assert definition["key"] == "gridConnectionPower"
    assert definition["icon_on"] == icon_on
    assert definition["icon_off"] == icon_off
    assert definition["device_class"] is None

    # -2246 W is importing from the grid: feed-in off, consuming on.
    expected_icon = icon_off if key == "grid_feed_in" else icon_on
    sensor = _sensor(key, _grid_power(-2246))
    assert sensor.unique_id == f"TEST-SN_{key}"
    assert sensor.icon == expected_icon


@pytest.mark.parametrize(
    "definitions",
    [STREAM_ULTRA_X_SENSOR_DEFINITIONS, STREAM_AC_PRO_SENSOR_DEFINITIONS],
    ids=["ultra_x", "ac_pro"],
)
@pytest.mark.parametrize("value", [-2246, 0, 200])
def test_numeric_grid_power_keeps_original_sign(definitions, value):
    sensor = EcoFlowSensor(
        coordinator=_coordinator(_grid_power(value)),
        entry=SimpleNamespace(entry_id="test-entry"),
        sensor_id="grid_connection_power",
        sensor_config=definitions["grid_connection_power"],
    )
    assert sensor.native_value == value
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT


def test_stream_micro_positive_export_convention_preserved():
    assert "grid_feeding" in STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS
    assert "grid_consuming" not in STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS
    assert "grid_connection_power" in STREAM_MICRO_INVERTER_SENSOR_DEFINITIONS

    feeding = _sensor(
        "grid_feeding",
        _grid_power(200),
        STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS,
        DEVICE_TYPE_STREAM_MICRO_INVERTER,
    )
    importing = _sensor(
        "grid_feeding",
        _grid_power(-200),
        STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS,
        DEVICE_TYPE_STREAM_MICRO_INVERTER,
    )
    boundary = _sensor(
        "grid_feeding",
        _grid_power(10),
        STREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS,
        DEVICE_TYPE_STREAM_MICRO_INVERTER,
    )
    assert feeding.is_on is True
    assert importing.is_on is False
    assert boundary.is_on is False


def test_powerstream_definitions_unchanged_and_not_grid_direction():
    definitions = POWERSTREAM_MICRO_INVERTER_BINARY_SENSOR_DEFINITIONS
    assert "feed_in_control" in definitions
    assert definitions["feed_in_control"]["key"] == "20_1.feedProtect"
    assert "grid_feed_in" not in definitions
    assert "grid_consuming" not in definitions
