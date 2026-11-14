"""Regression coverage for EcoFlowIntegralEnergySensor constructor changes.

home-assistant/core PR #177596 ("Do not set a device on YAML integration
entities", merged 2026-07-30) removed the ``hass`` parameter from
``homeassistant.components.integration.sensor.IntegrationSensor.__init__``.
Because ``IntegrationSensor`` is treated as internal API by Home Assistant
core, this change was not listed on the official breaking-changes page, so
integrations subclassing it (like ``EcoFlowIntegralEnergySensor``) started
raising ``TypeError: __init__() got an unexpected keyword argument 'hass'``
at entity-creation time as soon as a user upgraded to HA 2026.8, with no
prior warning.

These tests exercise the real construction path against whatever
``homeassistant`` version is installed, and also verify that ``hass`` is
still forwarded when the installed ``IntegrationSensor`` predates the
breaking change. HA 2026.11 also requires a device_class keyword.
"""

from __future__ import annotations

from inspect import signature

from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.ecoflow_api.sensor import EcoFlowIntegralEnergySensor


class _FakePowerSensor:
    """Minimal stand-in for the power SensorEntity used as integration source."""

    name = "Test Power"
    entity_id = "sensor.test_power"
    unique_id = "test_power_uid"
    device_info = None


async def test_energy_sensor_can_be_constructed(tmp_path) -> None:
    """EcoFlowIntegralEnergySensor must construct cleanly against the
    installed IntegrationSensor, regardless of whether it still accepts a
    `hass` keyword argument (pre- vs post-HA-2026.8)."""
    power_sensor = _FakePowerSensor()

    hass = HomeAssistant(str(tmp_path))
    # Only older constructors look up the source device during construction.
    if "hass" in signature(IntegrationSensor.__init__).parameters:
        hass.data[dr.DATA_REGISTRY] = dr.DeviceRegistry(hass)
        await dr.async_load(hass, load_empty=True)
        await er.async_load(hass, load_empty=True)
    sensor = EcoFlowIntegralEnergySensor(hass, power_sensor, enabled_default=True)

    assert sensor.name == "Test Power Energy"
    assert sensor.unique_id == "test_power_uid_energy"


def test_hass_still_forwarded_when_supported(monkeypatch) -> None:
    """When the installed IntegrationSensor still accepts `hass` (pre-2026.8
    behavior), EcoFlowIntegralEnergySensor must still pass it through."""
    received = {}

    def fake_init(
        self,
        *,
        hass,
        integration_method,
        name,
        round_digits,
        source_entity,
        unique_id,
        unit_prefix,
        unit_time,
        max_sub_interval,
    ):
        received["hass"] = hass

    monkeypatch.setattr(IntegrationSensor, "__init__", fake_init)

    fake_hass = object()
    power_sensor = _FakePowerSensor()
    EcoFlowIntegralEnergySensor(fake_hass, power_sensor)

    assert received["hass"] is fake_hass


def test_hass_omitted_when_unsupported(monkeypatch) -> None:
    """When the installed IntegrationSensor no longer accepts `hass` (HA
    2026.8+ behavior), EcoFlowIntegralEnergySensor must not pass it, since
    doing so raises TypeError."""
    received = {}

    def fake_init(
        self,
        *,
        integration_method,
        name,
        round_digits,
        source_entity,
        unique_id,
        unit_prefix,
        unit_time,
        max_sub_interval,
        device=None,
    ):
        received["called"] = True

    monkeypatch.setattr(IntegrationSensor, "__init__", fake_init)

    power_sensor = _FakePowerSensor()
    EcoFlowIntegralEnergySensor(object(), power_sensor)

    assert received.get("called") is True


def test_device_class_forwarded_when_required(monkeypatch) -> None:
    """HA 2026.11 requires an explicit device class, even for auto-detection."""
    received = {}

    def fake_init(
        self,
        *,
        integration_method,
        name,
        round_digits,
        source_entity,
        unique_id,
        device_class,
        unit_prefix,
        unit_time,
        max_sub_interval,
        device=None,
    ):
        received["device_class"] = device_class

    monkeypatch.setattr(IntegrationSensor, "__init__", fake_init)
    EcoFlowIntegralEnergySensor(object(), _FakePowerSensor())

    assert received == {"device_class": None}
