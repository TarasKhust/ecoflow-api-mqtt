"""Regression coverage for PowerStream 800W Custom Load Power max (issue #79).

The permanent_watts (Custom Load Power) slider was hardcoded to max 600 W,
blocking 800 W models. Its maximum now follows the device-reported
20_1.ratedPower (deciwatts) with a conservative 600 W fallback and an 800 W
upper bound, and tracks coordinator updates at runtime.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from custom_components.ecoflow_api.number import (
    EcoFlowPowerstreamNumber,
    POWERSTREAM_MICRO_INVERTER_NUMBER_DEFINITIONS,
    powerstream_permanent_watts_max,
)

DEFS = POWERSTREAM_MICRO_INVERTER_NUMBER_DEFINITIONS


def make_entity(
    data: dict[str, Any] | None, key: str = "permanent_watts"
) -> tuple[EcoFlowPowerstreamNumber, SimpleNamespace]:
    """Build the real entity with a fake coordinator (no I/O)."""
    coordinator = SimpleNamespace(
        device_sn="SN", command_sn="SN", data=data, calls=[]
    )

    async def fake_send(command: dict[str, Any]) -> dict[str, Any]:
        coordinator.calls.append(command)
        return {"ok": True}

    async def fake_refresh() -> None:
        return None

    coordinator.async_send_command = fake_send
    coordinator.async_request_refresh = fake_refresh
    entry = SimpleNamespace(entry_id="test_entry")
    return EcoFlowPowerstreamNumber(coordinator, entry, key, DEFS[key]), coordinator


def test_rated_600_flat_and_nested() -> None:
    """600 W models keep max 600 in both payload shapes."""
    assert powerstream_permanent_watts_max({"20_1.ratedPower": 6000}) == 600
    assert powerstream_permanent_watts_max({"20_1": {"ratedPower": 6000}}) == 600
    entity, _ = make_entity({"20_1.ratedPower": 6000})
    assert entity.native_max_value == 600


def test_rated_800_flat_and_nested() -> None:
    """800 W models unlock max 800 in both payload shapes."""
    assert powerstream_permanent_watts_max({"20_1.ratedPower": 8000}) == 800
    assert powerstream_permanent_watts_max({"20_1": {"ratedPower": 8000}}) == 800
    entity, _ = make_entity({"20_1": {"ratedPower": 8000}})
    assert entity.native_max_value == 800


def test_missing_rated_falls_back_to_600() -> None:
    """Absent rating (or no data at all) keeps the conservative 600 W max."""
    assert powerstream_permanent_watts_max({}) == 600
    assert powerstream_permanent_watts_max(None) == 600
    entity, _ = make_entity({})
    assert entity.native_max_value == 600


def test_malformed_rated_falls_back_to_600() -> None:
    """Non-numeric ratings never poison the slider maximum."""
    for bad in ("abc", "", [8000], {"v": 8000}, object()):
        assert powerstream_permanent_watts_max({"20_1.ratedPower": bad}) == 600


def test_nonfinite_rated_falls_back_to_600() -> None:
    """NaN/inf readings fall back instead of breaking the slider."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        assert powerstream_permanent_watts_max({"20_1.ratedPower": bad}) == 600


def test_boolean_rated_falls_back_to_600() -> None:
    """Booleans must not be coerced through float() into a limit."""
    assert powerstream_permanent_watts_max({"20_1.ratedPower": True}) == 600
    assert powerstream_permanent_watts_max({"20_1.ratedPower": False}) == 600


def test_out_of_range_rated_is_clamped_or_fallback() -> None:
    """Zero/negative fall back to 600; above-range clamps to the 800 cap."""
    for bad in (0, -50, "0"):
        assert powerstream_permanent_watts_max({"20_1.ratedPower": bad}) == 600
    for high in (8500, 9000, "9000"):
        assert powerstream_permanent_watts_max({"20_1.ratedPower": high}) == 800


def test_rating_updates_track_coordinator_data_at_runtime() -> None:
    """A rating that arrives (or disappears) later updates the max in place."""
    entity, coordinator = make_entity({})
    assert entity.native_max_value == 600
    coordinator.data = {"20_1": {"ratedPower": 8000}}
    assert entity.native_max_value == 800
    coordinator.data = {}
    assert entity.native_max_value == 600


def test_other_powerstream_numbers_keep_static_maximums() -> None:
    """Only permanent_watts is dynamic; sibling maximums never move."""
    for key, expected in (
        ("lower_limit", 30),
        ("upper_limit", 100),
        ("inv_brightness", 1023),
    ):
        for data in ({"20_1": {"ratedPower": 8000}}, {}):
            entity, _ = make_entity(data, key=key)
            assert entity.native_max_value == expected


def test_definition_base_max_stays_600() -> None:
    """The static definition keeps max 600 as the base/fallback value."""
    assert DEFS["permanent_watts"]["max"] == 600
    assert DEFS["permanent_watts"]["min"] == 0
    assert DEFS["permanent_watts"]["step"] == 10


async def test_outgoing_800w_command_sends_8000() -> None:
    """Setting 800 W in the UI must emit permanentWatts 8000 to the device."""
    entity, coordinator = make_entity({"20_1.ratedPower": 8000})
    await entity.async_set_native_value(800)
    assert coordinator.calls == [
        {
            "sn": "SN",
            "cmdCode": "WN511_SET_PERMANENT_WATTS_PACK",
            "params": {"permanentWatts": 8000},
        }
    ]


def test_oversized_integer_rated_falls_back_to_600() -> None:
    """Integers too large for float() must fall back, not raise."""
    assert powerstream_permanent_watts_max({"20_1.ratedPower": 10**1000}) == 600
