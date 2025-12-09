"""Number platform for EcoFlow API integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode, NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Number definitions for Delta Pro 3
DELTA_PRO_3_NUMBER_DEFINITIONS = {
    "ac_chg_power": {
        "name": "AC Charging Power",
        "key": "acChgPower",
        "min": 200,
        "max": 3000,
        "step": 100,
        "unit": UnitOfPower.WATT,
        "device_class": NumberDeviceClass.POWER,
        "icon": "mdi:lightning-bolt",
        "mode": NumberMode.SLIDER,
        "method": "async_set_ac_charging_power",
    },
    "max_chg_soc": {
        "name": "Max Charge Level",
        "key": "maxChgSoc",
        "min": 50,
        "max": 100,
        "step": 1,
        "unit": PERCENTAGE,
        "device_class": NumberDeviceClass.BATTERY,
        "icon": "mdi:battery-charging-90",
        "mode": NumberMode.SLIDER,
        "method": "async_set_max_charge_level",
    },
    "min_dsg_soc": {
        "name": "Min Discharge Level",
        "key": "minDsgSoc",
        "min": 0,
        "max": 30,
        "step": 1,
        "unit": PERCENTAGE,
        "device_class": NumberDeviceClass.BATTERY,
        "icon": "mdi:battery-charging-10",
        "mode": NumberMode.SLIDER,
        "method": "async_set_min_discharge_level",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow number entities.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowNumber] = []
    
    for number_key, number_def in DELTA_PRO_3_NUMBER_DEFINITIONS.items():
        entities.append(
            EcoFlowNumber(
                coordinator=coordinator,
                number_key=number_key,
                number_def=number_def,
            )
        )
        _LOGGER.debug("Adding number: %s", number_def["name"])

    async_add_entities(entities)
    _LOGGER.info("Added %d numbers for %s", len(entities), coordinator.device_sn)


class EcoFlowNumber(EcoFlowBaseEntity, NumberEntity):
    """EcoFlow number entity."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        number_key: str,
        number_def: dict[str, Any],
    ) -> None:
        """Initialize the number entity.
        
        Args:
            coordinator: Data update coordinator
            number_key: Unique key for this number
            number_def: Number definition dictionary
        """
        super().__init__(coordinator, number_key)
        
        self._number_def = number_def
        self._data_key = number_def.get("key", number_key)
        self._method_name = number_def["method"]
        
        # Set entity attributes from definition
        self._attr_name = number_def["name"]
        self._attr_native_min_value = number_def["min"]
        self._attr_native_max_value = number_def["max"]
        self._attr_native_step = number_def["step"]
        self._attr_native_unit_of_measurement = number_def.get("unit")
        self._attr_device_class = number_def.get("device_class")
        self._attr_icon = number_def.get("icon")
        self._attr_mode = number_def.get("mode", NumberMode.AUTO)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None
            
        value = self.coordinator.data.get(self._data_key)
        
        if value is None:
            return None
            
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value.
        
        Args:
            value: New value to set
        """
        _LOGGER.info(
            "Setting %s to %s for %s",
            self._attr_name,
            value,
            self.coordinator.device_sn
        )
        
        method = getattr(self.coordinator, self._method_name)
        await method(int(value))


