"""Regression coverage for the Delta Pro Ultra Network Type sensor."""

from types import SimpleNamespace

import pytest

from custom_components.ecoflow_api.sensor import (
    DELTA_PRO_ULTRA_SENSOR_DEFINITIONS,
    EcoFlowSensor,
)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"hs_yj751_pd_appshow_addr.wireless4GSta": 0}, 0),
        ({"hs_yj751_pd_appshow_addr": {"wireless4GSta": 7}}, 7),
        ({"hs_yj751_pd_appshow_addr": {}}, None),
    ],
)
def test_network_type_state(data, expected):
    sensor = EcoFlowSensor(
        SimpleNamespace(data=data, device_sn="test-device"),
        SimpleNamespace(entry_id="test-entry"),
        "wireless_4g_sta",
        DELTA_PRO_ULTRA_SENSOR_DEFINITIONS["wireless_4g_sta"],
    )
    sensor.entity_id = "sensor.delta_pro_ultra_network_type"
    sensor._attr_translation_key = None  # This test runs without an entity platform.

    # Read HA's state property to exercise the validation that failed on startup.
    assert sensor.state == expected
