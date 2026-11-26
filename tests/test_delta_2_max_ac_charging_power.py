"""Delta 2 Max AC charging power lives on the inverter module, not MPPT."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from custom_components.ecoflow_api import number as number_module
from custom_components.ecoflow_api.number import (
    DELTA_2_MAX_NUMBER_DEFINITIONS,
    DELTA_2_NUMBER_DEFINITIONS,
    EcoFlowDelta2Number,
)
from custom_components.ecoflow_api.sensor import (
    DELTA_2_MAX_SENSOR_DEFINITIONS,
    DELTA_2_SENSOR_DEFINITIONS,
)


class RecordingCoordinator:
    def __init__(self, data: dict[str, Any]) -> None:
        self.device_sn = "R351TEST"
        self.data = data
        self.commands: list[dict[str, Any]] = []

    async def async_send_command(self, payload: dict[str, Any]) -> None:
        self.commands.append(payload)

    async def async_request_refresh(self) -> None:
        return None


def _entity(number_def: dict[str, Any], data: dict[str, Any]) -> EcoFlowDelta2Number:
    entity = object.__new__(EcoFlowDelta2Number)
    entity.coordinator = RecordingCoordinator(data)
    entity._number_key = "ac_charging_power"
    entity._number_def = number_def
    return entity


def test_delta_2_keeps_mppt_mapping() -> None:
    number_def = DELTA_2_NUMBER_DEFINITIONS["ac_charging_power"]
    assert number_def["state_key"] == "mppt.cfgChgWatts"
    assert number_def["module_type"] == 5
    assert DELTA_2_SENSOR_DEFINITIONS["mppt_cfg_chg_watts"]["key"] == "mppt.cfgChgWatts"


def test_delta_2_max_limit_sensor_reads_inverter() -> None:
    sensor_def = DELTA_2_MAX_SENSOR_DEFINITIONS["mppt_cfg_chg_watts"]
    assert sensor_def["key"] == "inv.SlowChgWatts"
    assert sensor_def["name"] == "AC Charging Power Limit"


def test_delta_2_max_reads_inverter_slow_charge_watts() -> None:
    number_def = DELTA_2_MAX_NUMBER_DEFINITIONS["ac_charging_power"]
    entity = _entity(number_def, {"inv.SlowChgWatts": 1000, "inv.FastChgWatts": 2400})
    assert entity.native_value == 1000.0
    assert number_def["max"] == 2400


async def test_delta_2_max_sends_inverter_command(monkeypatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(number_module.asyncio, "sleep", no_sleep)
    entity = _entity(
        DELTA_2_MAX_NUMBER_DEFINITIONS["ac_charging_power"],
        {"inv.SlowChgWatts": 1000, "inv.FastChgWatts": 2400},
    )

    await entity.async_set_native_value(900)

    [payload] = entity.coordinator.commands
    assert payload["sn"] == "R351TEST"
    assert payload["moduleType"] == 3
    assert payload["operateType"] == "acChgCfg"
    assert payload["params"] == {
        "slowChgWatts": 900,
        "fastChgWatts": 2400,
        "chgPauseFlag": 0,
    }


async def test_delta_2_max_omits_fast_watts_when_unknown(monkeypatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(number_module.asyncio, "sleep", no_sleep)
    entity = _entity(DELTA_2_MAX_NUMBER_DEFINITIONS["ac_charging_power"], {})

    await entity.async_set_native_value(500)

    [payload] = entity.coordinator.commands
    assert payload["params"] == {"slowChgWatts": 500, "chgPauseFlag": 0}
