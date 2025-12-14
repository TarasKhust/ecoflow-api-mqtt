"""Binary sensor platform for EcoFlow API integration."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .const import DOMAIN
from .entity import EcoFlowBaseEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EcoFlowDataCoordinator

_LOGGER = logging.getLogger(__name__)


# Binary sensor definitions for Delta Pro 3
DELTA_PRO_3_BINARY_SENSOR_DEFINITIONS = {
    "ac_in_connected": {
        "name": "AC Input Connected",
        "key": "acInConnected",
        "device_class": BinarySensorDeviceClass.PLUG,
        "icon_on": "mdi:power-plug",
        "icon_off": "mdi:power-plug-off",
        "derived": True,
        "derive_from": "powGetAcIn",
        "derive_condition": lambda v: v is not None and v > 0,
    },
    "solar_connected": {
        "name": "Solar Input Connected",
        "key": "solarConnected",
        "device_class": BinarySensorDeviceClass.PLUG,
        "icon_on": "mdi:solar-power",
        "icon_off": "mdi:solar-power-variant-outline",
        "derived": True,
        "derive_from": "powGetPvH",
        "derive_condition": lambda v: v is not None and v > 0,
    },
    "is_charging": {
        "name": "Charging",
        "key": "isCharging",
        "device_class": BinarySensorDeviceClass.BATTERY_CHARGING,
        "icon_on": "mdi:battery-charging",
        "icon_off": "mdi:battery",
        "derived": True,
        "derive_from": "powInSumW",
        "derive_condition": lambda v: v is not None and v > 10,
    },
    "is_discharging": {
        "name": "Discharging",
        "key": "isDischarging",
        "device_class": BinarySensorDeviceClass.POWER,
        "icon_on": "mdi:battery-arrow-down",
        "icon_off": "mdi:battery",
        "derived": True,
        "derive_from": "powOutSumW",
        "derive_condition": lambda v: v is not None and v > 10,
    },
    "ac_out_enabled": {
        "name": "AC Output Enabled",
        "key": "acOutState",
        "device_class": BinarySensorDeviceClass.POWER,
        "icon_on": "mdi:power-socket",
        "icon_off": "mdi:power-socket-off",
        "derived": False,
    },
    "dc_out_enabled": {
        "name": "DC Output Enabled",
        "key": "dcOutState",
        "device_class": BinarySensorDeviceClass.POWER,
        "icon_on": "mdi:current-dc",
        "icon_off": "mdi:current-dc",
        "derived": False,
    },
    "battery_low": {
        "name": "Battery Low",
        "key": "batteryLow",
        "device_class": BinarySensorDeviceClass.BATTERY,
        "icon_on": "mdi:battery-alert",
        "icon_off": "mdi:battery",
        "derived": True,
        "derive_from": "bmsBattSoc",
        "derive_condition": lambda v: v is not None and v < 20,
    },
    "battery_full": {
        "name": "Battery Full",
        "key": "batteryFull",
        "device_class": BinarySensorDeviceClass.BATTERY,
        "icon_on": "mdi:battery-check",
        "icon_off": "mdi:battery",
        "derived": True,
        "derive_from": "bmsBattSoc",
        "derive_condition": lambda v: v is not None and v >= 100,
    },
    "over_temp": {
        "name": "Over Temperature",
        "key": "overTemp",
        "device_class": BinarySensorDeviceClass.HEAT,
        "icon_on": "mdi:thermometer-alert",
        "icon_off": "mdi:thermometer",
        "derived": True,
        "derive_from": "bmsMaxCellTemp",
        "derive_condition": lambda v: v is not None and v > 45,
    },
}

# Extra Battery binary sensor definitions
EXTRA_BATTERY_BINARY_SENSOR_DEFINITIONS = {
    "connected": {
        "name": "Connected",
        "device_class": BinarySensorDeviceClass.CONNECTIVITY,
        "icon_on": "mdi:battery-plus",
        "icon_off": "mdi:battery-off",
        "check_key": "Soc",  # If we have SOC data, battery is connected
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

# Possible prefixes for extra battery data in API response
EXTRA_BATTERY_PREFIXES = [
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


def _detect_extra_batteries(data: dict[str, Any]) -> list[str]:
    """Detect extra battery prefixes in API response data.

    Args:
        data: API response data

    Returns:
        List of found battery prefixes
    """
    if not data:
        return []

    found_prefixes: set[str] = set()

    for key in data:
        for prefix in EXTRA_BATTERY_PREFIXES:
            if key.startswith(prefix):
                found_prefixes.add(prefix)

    return sorted(found_prefixes)


def _get_battery_number(prefix: str) -> int:
    """Extract battery number from prefix."""
    match = re.search(r"(\d+)", prefix)
    if match:
        return int(match.group(1))
    return 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow binary sensor entities.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    # Add main device binary sensors
    for sensor_key, sensor_def in DELTA_PRO_3_BINARY_SENSOR_DEFINITIONS.items():
        entities.append(
            EcoFlowBinarySensor(
                coordinator=coordinator,
                sensor_key=sensor_key,
                sensor_def=sensor_def,
            )
        )

    # Detect and add extra battery binary sensors
    if coordinator.data:
        extra_battery_prefixes = _detect_extra_batteries(coordinator.data)
        _LOGGER.info(
            "Detected %d extra batteries for binary sensors",
            len(extra_battery_prefixes),
        )

        for prefix in extra_battery_prefixes:
            battery_num = _get_battery_number(prefix)

            for (
                sensor_key,
                sensor_def,
            ) in EXTRA_BATTERY_BINARY_SENSOR_DEFINITIONS.items():
                entities.append(
                    EcoFlowExtraBatteryBinarySensor(
                        coordinator=coordinator,
                        battery_prefix=prefix,
                        battery_number=battery_num,
                        sensor_key=sensor_key,
                        sensor_def=sensor_def,
                    )
                )

    async_add_entities(entities)
    _LOGGER.info("Added %d binary sensors for %s", len(entities), coordinator.device_sn)


class EcoFlowBinarySensor(EcoFlowBaseEntity, BinarySensorEntity):
    """EcoFlow binary sensor entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        sensor_key: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data update coordinator
            sensor_key: Unique key for this sensor
            sensor_def: Sensor definition dictionary
        """
        super().__init__(coordinator, sensor_key)

        self._sensor_def = sensor_def
        self._data_key = sensor_def.get("key", sensor_key)
        self._is_derived = sensor_def.get("derived", False)
        self._derive_from = sensor_def.get("derive_from")
        self._derive_condition = sensor_def.get("derive_condition")

        # Set entity attributes from definition
        self._attr_name = sensor_def["name"]
        self._attr_device_class = sensor_def.get("device_class")
        self._icon_on = sensor_def.get("icon_on", "mdi:check-circle")
        self._icon_off = sensor_def.get("icon_off", "mdi:circle-outline")

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        # Handle derived sensors
        if self._is_derived and self._derive_from and self._derive_condition:
            source_value = self.coordinator.data.get(self._derive_from)
            return self._derive_condition(source_value)

        # Handle direct state sensors
        value = self.coordinator.data.get(self._data_key)

        if value is None:
            return None

        # Handle different value types
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.lower() in ("1", "true", "on")

        return None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return self._icon_on
        return self._icon_off


class EcoFlowExtraBatteryBinarySensor(EcoFlowBaseEntity, BinarySensorEntity):
    """EcoFlow Extra Battery binary sensor entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        battery_prefix: str,
        battery_number: int,
        sensor_key: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the extra battery binary sensor.

        Args:
            coordinator: Data update coordinator
            battery_prefix: Battery prefix (e.g., "slave1")
            battery_number: Battery number (1, 2, etc.)
            sensor_key: Sensor key (e.g., "connected")
            sensor_def: Sensor definition dictionary
        """
        entity_key = f"extra_battery_{battery_number}_{sensor_key}"
        super().__init__(coordinator, entity_key)

        self._battery_prefix = battery_prefix
        self._battery_number = battery_number
        self._sensor_key = sensor_key
        self._sensor_def = sensor_def
        self._check_key = f"{battery_prefix}{sensor_def.get('check_key', 'Soc')}"
        self._condition = sensor_def.get("condition")

        # Set entity attributes
        self._attr_name = f"Extra Battery {battery_number} {sensor_def['name']}"
        self._attr_device_class = sensor_def.get("device_class")
        self._icon_on = sensor_def.get("icon_on", "mdi:check-circle")
        self._icon_off = sensor_def.get("icon_off", "mdi:circle-outline")

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._check_key)

        # For "connected" sensor, check if we have data
        if self._sensor_key == "connected":
            return value is not None

        # For conditional sensors
        if self._condition:
            return self._condition(value)

        return None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return self._icon_on
        return self._icon_off

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "battery_number": self._battery_number,
            "battery_prefix": self._battery_prefix,
        }
