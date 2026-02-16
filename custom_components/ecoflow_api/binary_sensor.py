"""Binary sensor platform for EcoFlow API integration."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import TypedDict

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowBinarySensorDef
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


class _ExtraBatterySensorDef(TypedDict, total=False):
    """Type definition for extra battery sensor configuration."""

    name: str
    device_class: BinarySensorDeviceClass
    icon_on: str
    icon_off: str
    check_key: str
    condition: Callable[[int | float | None], bool]


# Extra Battery binary sensor definitions (shared across devices)
_EXTRA_BATTERY_BINARY_SENSORS: dict[str, _ExtraBatterySensorDef] = {
    "connected": {
        "name": "Connected",
        "device_class": BinarySensorDeviceClass.CONNECTIVITY,
        "icon_on": "mdi:battery-plus",
        "icon_off": "mdi:battery-off",
        "check_key": "Soc",
    },
    "battery_low": {
        "name": "Battery Low",
        "device_class": BinarySensorDeviceClass.BATTERY,
        "icon_on": "mdi:battery-alert",
        "icon_off": "mdi:battery",
        "check_key": "Soc",
        "condition": lambda v: v is not None and v < 20,
    },
    "battery_full": {
        "name": "Battery Full",
        "device_class": BinarySensorDeviceClass.BATTERY,
        "icon_on": "mdi:battery-check",
        "icon_off": "mdi:battery",
        "check_key": "Soc",
        "condition": lambda v: v is not None and v >= 100,
    },
    "over_temp": {
        "name": "Over Temperature",
        "device_class": BinarySensorDeviceClass.HEAT,
        "icon_on": "mdi:thermometer-alert",
        "icon_off": "mdi:thermometer",
        "check_key": "Temp",
        "condition": lambda v: v is not None and v > 45,
    },
}

_EXTRA_BATTERY_PREFIXES = [
    "slave1",
    "slave2",
    "slave3",
    "bms2",
    "bms3",
    "eb1",
    "eb2",
    "extraBms",
    "slaveBattery",
]


def _detect_extra_batteries(data: dict[str, object]) -> list[str]:
    if not data:
        return []
    found: set[str] = set()
    for key in data:
        for prefix in _EXTRA_BATTERY_PREFIXES:
            if key.startswith(prefix):
                found.add(prefix)
    return sorted(found)


def _get_battery_number(prefix: str) -> int:
    match = re.search(r"(\d+)", prefix)
    return int(match.group(1)) if match else 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow binary sensor entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    entities: list[BinarySensorEntity] = []

    # Add profile-defined binary sensors
    if profile and profile.binary_sensors:
        entities.extend(EcoFlowBinarySensor(coordinator, defn) for defn in profile.binary_sensors)

    # Detect and add extra battery binary sensors
    if coordinator.data:
        extra_prefixes = _detect_extra_batteries(coordinator.data)
        for prefix in extra_prefixes:
            battery_num = _get_battery_number(prefix)
            for sensor_key, sensor_def in _EXTRA_BATTERY_BINARY_SENSORS.items():
                entities.append(
                    EcoFlowExtraBatteryBinarySensor(coordinator, prefix, battery_num, sensor_key, sensor_def)
                )

    async_add_entities(entities)
    _LOGGER.debug("Added %d binary sensors for %s", len(entities), coordinator.device_sn)


class EcoFlowBinarySensor(EcoFlowBaseEntity, BinarySensorEntity):
    """EcoFlow binary sensor entity."""

    def __init__(self, coordinator: EcoFlowDataCoordinator, defn: EcoFlowBinarySensorDef) -> None:
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._attr_name = defn.name
        self._attr_device_class = defn.device_class
        self._icon_on = defn.icon_on or "mdi:check-circle"
        self._icon_off = defn.icon_off or "mdi:circle-outline"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None

        # Handle derived sensors
        if self._defn.derived:
            source_key = self._defn.derive_from or self._defn.state_key
            source_value = self.coordinator.data.get(source_key)
            if self._defn.derive_condition:
                return self._defn.derive_condition(source_value)
            return None

        # Handle direct state sensors
        value = self.coordinator.data.get(self._defn.state_key)
        if value is None:
            return None

        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.lower() in ("1", "true", "on")
        return None

    @property
    def icon(self) -> str:
        return self._icon_on if self.is_on else self._icon_off


class EcoFlowExtraBatteryBinarySensor(EcoFlowBaseEntity, BinarySensorEntity):
    """EcoFlow Extra Battery binary sensor entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        battery_prefix: str,
        battery_number: int,
        sensor_key: str,
        sensor_def: _ExtraBatterySensorDef,
    ) -> None:
        entity_key = f"extra_battery_{battery_number}_{sensor_key}"
        super().__init__(coordinator, entity_key)
        self._battery_prefix = battery_prefix
        self._battery_number = battery_number
        self._sensor_key = sensor_key
        self._sensor_def = sensor_def
        self._check_key = f"{battery_prefix}{sensor_def.get('check_key', 'Soc')}"
        self._condition = sensor_def.get("condition")
        self._attr_name = f"Extra Battery {battery_number} {sensor_def['name']}"
        self._attr_device_class = sensor_def.get("device_class")
        self._icon_on = sensor_def.get("icon_on", "mdi:check-circle")
        self._icon_off = sensor_def.get("icon_off", "mdi:circle-outline")

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self._check_key)
        if self._sensor_key == "connected":
            return value is not None
        if self._condition:
            return self._condition(value)
        return None

    @property
    def icon(self) -> str:
        return self._icon_on if self.is_on else self._icon_off

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        return {
            "battery_number": self._battery_number,
            "battery_prefix": self._battery_prefix,
        }
