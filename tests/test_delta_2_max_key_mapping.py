"""Delta 2 Max entities must read keys the Max actually reports."""

from __future__ import annotations

from custom_components.ecoflow_api.binary_sensor import (
    DELTA_2_BINARY_SENSOR_DEFINITIONS,
    DELTA_2_MAX_BINARY_SENSOR_DEFINITIONS,
)
from custom_components.ecoflow_api.number import (
    DELTA_2_MAX_NUMBER_DEFINITIONS,
    DELTA_2_NUMBER_DEFINITIONS,
)
from custom_components.ecoflow_api.select import (
    DELTA_2_MAX_SELECT_DEFINITIONS,
    DELTA_2_SELECT_DEFINITIONS,
)
from custom_components.ecoflow_api.sensor import (
    DELTA_2_MAX_SENSOR_DEFINITIONS,
    DELTA_2_SENSOR_DEFINITIONS,
)


def test_binary_sensors_read_inverter_and_pd_keys() -> None:
    keys = {k: v["key"] for k, v in DELTA_2_MAX_BINARY_SENSOR_DEFINITIONS.items()}
    assert keys["ac_out_enabled"] == "inv.cfgAcEnabled"
    assert keys["x_boost_enabled"] == "inv.cfgAcXboost"
    assert keys["beeper_silent"] == "pd.beepMode"
    # Delta 2 keeps its MPPT keys
    assert DELTA_2_BINARY_SENSOR_DEFINITIONS["ac_out_enabled"]["key"] == "mppt.cfgAcEnabled"


def test_sensor_keys_renamed_on_max() -> None:
    assert DELTA_2_MAX_SENSOR_DEFINITIONS["inv_standby_mins"]["key"] == "inv.standbyMin"
    assert DELTA_2_MAX_SENSOR_DEFINITIONS["pd_min_ac_out_soc"]["key"] == "pd.minAcSoc"
    assert DELTA_2_MAX_SENSOR_DEFINITIONS["pd_pv_chg_prio_set"]["key"] == "pd.pvChargePrioSet"
    assert DELTA_2_SENSOR_DEFINITIONS["inv_standby_mins"]["key"] == "inv.standbyMins"


def test_max_controls() -> None:
    assert "ac_standby_time" not in DELTA_2_MAX_NUMBER_DEFINITIONS
    assert "ac_standby_time" in DELTA_2_NUMBER_DEFINITIONS
    assert DELTA_2_MAX_SELECT_DEFINITIONS["solar_priority"]["state_key"] == "pd.pvChargePrioSet"
    assert DELTA_2_SELECT_DEFINITIONS["solar_priority"]["state_key"] == "pd.pvChgPrioSet"


def test_unreported_sensors_dropped_on_max_only() -> None:
    dropped = {"mppt_cfg_ac_enabled", "mppt_beep_state", "pd_ext_rj45_port", "pd_charger_type"}
    assert dropped.isdisjoint(DELTA_2_MAX_SENSOR_DEFINITIONS)
    assert dropped <= set(DELTA_2_SENSOR_DEFINITIONS)
