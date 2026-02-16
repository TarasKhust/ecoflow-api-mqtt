"""Sensor platform for EcoFlow API integration."""

from __future__ import annotations

import logging
import struct
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile
from .devices.base import EcoFlowSensorDef
from .entity import EcoFlowBaseEntity
from .hybrid_coordinator import EcoFlowHybridCoordinator

_LOGGER = logging.getLogger(__name__)

# Sensor keys that should get automatic energy integration
_ENERGY_INTEGRATION_KEYS = {
    "pow_in_sum_w": True,  # Total Input Power - enabled by default
    "pow_out_sum_w": True,  # Total Output Power - enabled by default
    "pow_get_ac_in": False,  # AC Input Power - disabled by default
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow sensor entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    profile = get_profile(coordinator.device_type)

    if not profile:
        return

    entities: list[SensorEntity] = []

    # Add profile-defined sensors
    entities.extend(EcoFlowSensor(coordinator, defn) for defn in profile.sensors)

    # Add MQTT status/mode sensors if using hybrid coordinator
    if isinstance(coordinator, EcoFlowHybridCoordinator):
        entities.append(EcoFlowMQTTStatusSensor(coordinator, entry))
        entities.append(EcoFlowMQTTModeSensor(coordinator, entry))
        _LOGGER.info("Added MQTT status sensors for hybrid coordinator")

    async_add_entities(entities)
    _LOGGER.info("Added %d sensor entities for %s", len(entities), profile.device_type)

    # Add energy integration sensors (for HA Energy Dashboard)
    _setup_energy_sensors(hass, coordinator, entities, async_add_entities)


def _setup_energy_sensors(
    hass: HomeAssistant,
    coordinator: EcoFlowDataCoordinator,
    entities: list[SensorEntity],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up energy integration sensors for power sensors."""
    energy_sensors: list[SensorEntity] = []
    total_input_sensor: EcoFlowSensor | None = None
    total_output_sensor: EcoFlowSensor | None = None

    for sensor in entities:
        if not isinstance(sensor, EcoFlowSensor):
            continue

        key = sensor.definition.key

        if key in _ENERGY_INTEGRATION_KEYS:
            energy_sensors.append(
                EcoFlowIntegralEnergySensor(hass, sensor, enabled_default=_ENERGY_INTEGRATION_KEYS[key])
            )

        if key == "pow_in_sum_w":
            total_input_sensor = sensor
        elif key == "pow_out_sum_w":
            total_output_sensor = sensor

    # Add power difference sensor (for HA Energy "Now" tab)
    if total_input_sensor and total_output_sensor:
        energy_sensors.append(
            EcoFlowPowerDifferenceSensor(
                coordinator=coordinator,
                input_sensor=total_input_sensor,
                output_sensor=total_output_sensor,
            )
        )
        _LOGGER.info("Created power difference sensor for energy dashboard")

    if energy_sensors:
        async_add_entities(energy_sensors)
        _LOGGER.info(
            "Added %d energy sensors for Home Assistant Energy Dashboard",
            len(energy_sensors),
        )


# ============================================================================
# Standard Sensor
# ============================================================================


class EcoFlowSensor(EcoFlowBaseEntity, SensorEntity):
    """Unified EcoFlow sensor entity driven by EcoFlowSensorDef."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        defn: EcoFlowSensorDef,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, defn.key)
        self._defn = defn
        self._attr_name = defn.name
        self._attr_native_unit_of_measurement = defn.unit
        self._attr_device_class = defn.device_class
        self._attr_state_class = defn.state_class
        self._attr_icon = defn.icon
        self._attr_entity_category = defn.entity_category

        # Handle ENUM sensors
        if defn.device_class == SensorDeviceClass.ENUM and defn.options:
            self._attr_options = defn.options

    @property
    def definition(self) -> EcoFlowSensorDef:
        """Return the sensor definition."""
        return self._defn

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        state_key = self._defn.state_key
        value = self.coordinator.data.get(state_key)

        # Handle nested object fallback for dotted keys
        if value is None and "." in state_key:
            parts = state_key.split(".", 1)
            parent = self.coordinator.data.get(parts[0])
            if isinstance(parent, dict):
                value = parent.get(parts[1])

        if value is None:
            return None

        # Handle resvInfo array sensors (extra battery data)
        if self._defn.resv_index is not None:
            return self._decode_resv_value(value)

        # Handle ENUM sensors - map integer values to option strings
        if self._defn.device_class == SensorDeviceClass.ENUM and self._defn.options:
            if isinstance(value, (int, float)):
                idx = int(value)
                options = self._defn.options
                # Try direct index first (0-based)
                if 0 <= idx < len(options):
                    return options[idx]
                # Try index-1 for 1-based API values
                if 1 <= idx <= len(options):
                    return options[idx - 1]
            return str(value) if value is not None else None

        # Handle timestamp
        if self._defn.device_class == SensorDeviceClass.TIMESTAMP:
            return self._parse_timestamp(value)

        # Convert boolean to string for text sensors
        if isinstance(value, bool):
            return "on" if value else "off"

        return value

    def _decode_resv_value(self, raw_value: Any) -> float | None:
        """Decode value from resvInfo array."""
        if not isinstance(raw_value, list):
            return None
        idx = self._defn.resv_index
        if idx is None or idx >= len(raw_value):
            return None

        raw_val = raw_value[idx]
        if raw_val == 0:
            return None  # No data available

        resv_type = self._defn.resv_type

        if resv_type == "float":
            # Decode IEEE 754 float from int
            try:
                decoded = struct.unpack("f", struct.pack("I", raw_val))[0]
                return round(decoded, 2)
            except (struct.error, OverflowError):
                return None
        elif resv_type == "mah_to_ah":
            # Convert mAh to Ah
            return round(raw_val / 1000, 2)

        return raw_val

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        """Parse timestamp value."""
        if value is None or value == 0 or value == "0":
            return None
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace(" ", "T"))
                if dt.tzinfo is None:
                    dt = dt_util.as_utc(dt)
                elif dt.tzinfo != dt_util.UTC:
                    dt = dt.astimezone(dt_util.UTC)
                return dt
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return dt_util.as_utc(value)
                if value.tzinfo != dt_util.UTC:
                    return value.astimezone(dt_util.UTC)
                return value
            if isinstance(value, (int, float)):
                ts = float(value)
                if ts > 946684800000:  # Year 2000 in milliseconds
                    ts = ts / 1000
                return dt_util.utc_from_timestamp(ts)
        except (ValueError, TypeError, OverflowError, OSError):
            _LOGGER.warning("Failed to parse timestamp '%s'", value)
        return None


# ============================================================================
# Energy Integration Sensors
# ============================================================================


class EcoFlowIntegralEnergySensor(IntegrationSensor):
    """Integration sensor that calculates energy (kWh) from power (W) sensors.

    Automatically integrates power sensors to provide energy consumption/generation
    compatible with Home Assistant Energy Dashboard.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_registry_visible_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        power_sensor: SensorEntity,
        enabled_default: bool = True,
    ):
        """Initialize energy sensor from power sensor."""
        super().__init__(
            hass=hass,
            integration_method="left",
            name=f"{power_sensor.name} Energy",
            round_digits=4,
            source_entity=power_sensor.entity_id,
            unique_id=f"{power_sensor.unique_id}_energy",
            unit_prefix="k",
            unit_time="h",
            max_sub_interval=timedelta(seconds=60),
        )
        # Copy device info from power sensor
        self._attr_device_info = power_sensor.device_info
        self._attr_entity_registry_enabled_default = enabled_default


class EcoFlowPowerDifferenceSensor(SensorEntity, EcoFlowBaseEntity):
    """Sensor that calculates power difference (input - output).

    Useful for Home Assistant Energy Dashboard to show net power flow.
    Positive = charging, Negative = discharging.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        input_sensor: SensorEntity,
        output_sensor: SensorEntity,
    ):
        """Initialize power difference sensor."""
        super().__init__(coordinator, "power_difference")
        self._attr_name = "Power Difference"
        self._attr_icon = "mdi:transmission-tower-export"

        self._input_sensor = input_sensor
        self._output_sensor = output_sensor
        self._difference: float | None = None
        self._states: dict[str, float | str] = {}

    async def async_added_to_hass(self) -> None:
        """Handle added to Hass."""
        await super().async_added_to_hass()

        source_entity_ids = [
            self._input_sensor.entity_id,
            self._output_sensor.entity_id,
        ]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                source_entity_ids,
                self._async_difference_sensor_state_listener,
            )
        )

        # Replay current state of source entities
        for entity_id in source_entity_ids:
            state = self.hass.states.get(entity_id)
            if state:
                state_event: Event[EventStateChangedData] = Event(
                    "", {"entity_id": entity_id, "new_state": state, "old_state": None}
                )
                self._async_difference_sensor_state_listener(state_event, update_state=False)

        self._calc_difference()

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._difference

    @callback
    def _async_difference_sensor_state_listener(
        self, event: Event[EventStateChangedData], update_state: bool = True
    ) -> None:
        """Handle the sensor state changes."""
        new_state = event.data["new_state"]
        entity = event.data["entity_id"]

        if new_state is None or new_state.state is None or new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            self._states[entity] = STATE_UNKNOWN
            if not update_state:
                return

            self._calc_difference()
            self.async_write_ha_state()
            return

        try:
            self._states[entity] = float(new_state.state)
        except ValueError:
            _LOGGER.warning(
                "Unable to store state for %s. Only numerical states are supported",
                entity,
            )
            return

        if not update_state:
            return

        self._calc_difference()
        self.async_write_ha_state()

    @callback
    def _calc_difference(self) -> None:
        """Calculate the power difference (input - output)."""
        if (
            self._states.get(self._input_sensor.entity_id) is STATE_UNKNOWN
            or self._states.get(self._output_sensor.entity_id) is STATE_UNKNOWN
        ):
            self._difference = None
            return

        # Power difference: input - output
        # Positive = charging/receiving power
        # Negative = discharging/consuming power
        input_power = float(self._states.get(self._input_sensor.entity_id, 0))
        output_power = float(self._states.get(self._output_sensor.entity_id, 0))
        self._difference = input_power - output_power


# ============================================================================
# MQTT Status Sensors
# ============================================================================


class EcoFlowMQTTStatusSensor(EcoFlowBaseEntity, SensorEntity):
    """Sensor for MQTT connection status."""

    def __init__(
        self,
        coordinator: EcoFlowHybridCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize MQTT status sensor."""
        super().__init__(coordinator, "mqtt_connection_status")
        self._coordinator = coordinator
        self._attr_name = "MQTT Connection Status"
        self._attr_unique_id = f"{entry.entry_id}_mqtt_connection_status"
        self._attr_icon = "mdi:cloud-check"

    @property
    def native_value(self) -> str:
        """Return MQTT connection status."""
        if self._coordinator.mqtt_connected:
            return "connected"
        return "disconnected"

    @property
    def icon(self) -> str:
        """Return icon based on connection status."""
        if self._coordinator.mqtt_connected:
            return "mdi:cloud-check"
        return "mdi:cloud-off"


class EcoFlowMQTTModeSensor(EcoFlowBaseEntity, SensorEntity):
    """Sensor for connection mode (hybrid/rest_only)."""

    def __init__(
        self,
        coordinator: EcoFlowHybridCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize connection mode sensor."""
        super().__init__(coordinator, "connection_mode")
        self._coordinator = coordinator
        self._attr_name = "Connection Mode"
        self._attr_unique_id = f"{entry.entry_id}_connection_mode"
        self._attr_icon = "mdi:connection"

    @property
    def native_value(self) -> str:
        """Return connection mode."""
        return self._coordinator.connection_mode

    @property
    def icon(self) -> str:
        """Return icon based on connection mode."""
        mode = self._coordinator.connection_mode
        if mode == "hybrid":
            return "mdi:connection"
        if mode == "mqtt_standby":
            return "mdi:cloud-sync"
        return "mdi:cloud-off"
