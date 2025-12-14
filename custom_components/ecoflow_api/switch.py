"""Switch platform for EcoFlow API integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .entity import EcoFlowBaseEntity

_LOGGER = logging.getLogger(__name__)


# Switch definitions for Delta Pro 3 based on API documentation
DELTA_PRO_3_SWITCH_DEFINITIONS = {
    "ac_hv_out": {
        "name": "AC HV Output",
        "state_key": "flowInfoAcHvOut",  # 0: off, 2: on
        "command_key": "cfgHvAcOutOpen",
        "icon_on": "mdi:power-plug",
        "icon_off": "mdi:power-plug-off",
        "device_class": SwitchDeviceClass.OUTLET,
    },
    "ac_lv_out": {
        "name": "AC LV Output",
        "state_key": "flowInfoAcLvOut",  # 0: off, 2: on
        "command_key": "cfgLvAcOutOpen",
        "icon_on": "mdi:power-plug",
        "icon_off": "mdi:power-plug-off",
        "device_class": SwitchDeviceClass.OUTLET,
    },
    "dc_12v_out": {
        "name": "12V DC Output",
        "state_key": "flowInfo12v",  # 0: off, 2: on
        "command_key": "cfgDc12vOutOpen",
        "icon_on": "mdi:car-battery",
        "icon_off": "mdi:car-battery",
        "device_class": SwitchDeviceClass.OUTLET,
    },
    "x_boost": {
        "name": "X-Boost",
        "state_key": "xboostEn",  # bool
        "command_key": "cfgXboostEn",
        "icon_on": "mdi:lightning-bolt",
        "icon_off": "mdi:lightning-bolt-outline",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "beeper": {
        "name": "Beeper",
        "state_key": "enBeep",  # bool
        "command_key": "cfgBeepEn",
        "icon_on": "mdi:volume-high",
        "icon_off": "mdi:volume-off",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "ac_energy_saving": {
        "name": "AC Energy Saving",
        "state_key": "acEnergySavingOpen",  # bool
        "command_key": "cfgAcEnergySavingOpen",
        "icon_on": "mdi:leaf",
        "icon_off": "mdi:leaf-off",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "generator_auto_start": {
        "name": "Generator Auto Start",
        "state_key": "cmsOilSelfStart",  # bool
        "command_key": "cfgCmsOilSelfStart",
        "icon_on": "mdi:engine",
        "icon_off": "mdi:engine-off",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "gfci": {
        "name": "GFCI",
        "state_key": "llcGFCIFlag",  # bool
        "command_key": "cfgLlcGFCIFlag",
        "icon_on": "mdi:shield-check",
        "icon_off": "mdi:shield-off",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "generator_pv_hybrid": {
        "name": "Generator PV Hybrid Mode",
        "state_key": "generatorPvHybridModeOpen",  # bool
        "command_key": "cfgGeneratorPvHybridModeOpen",
        "icon_on": "mdi:solar-power",
        "icon_off": "mdi:solar-power-outline",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    "generator_care_mode": {
        "name": "Generator Care Mode",
        "state_key": "generatorCareModeOpen",  # bool
        "command_key": "cfgGeneratorCareModeOpen",
        "icon_on": "mdi:weather-night",
        "icon_off": "mdi:weather-night-outline",
        "device_class": SwitchDeviceClass.SWITCH,
    },
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoFlow switch entities."""
    coordinator: EcoFlowDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[EcoFlowSwitch] = []
    
    for switch_key, switch_def in DELTA_PRO_3_SWITCH_DEFINITIONS.items():
        entities.append(
            EcoFlowSwitch(
                coordinator=coordinator,
                entry=entry,
                switch_key=switch_key,
                switch_def=switch_def,
            )
        )
    
    async_add_entities(entities)
    _LOGGER.info("Added %d switch entities", len(entities))


class EcoFlowSwitch(EcoFlowBaseEntity, SwitchEntity):
    """Representation of an EcoFlow switch."""

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entry: ConfigEntry,
        switch_key: str,
        switch_def: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, switch_key)
        self._switch_key = switch_key
        self._switch_def = switch_def
        self._attr_unique_id = f"{entry.entry_id}_{switch_key}"
        self._attr_name = switch_def["name"]
        self._attr_translation_key = switch_key
        self._attr_device_class = switch_def.get("device_class")

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if not self.coordinator.data:
            return None
        
        state_key = self._switch_def["state_key"]
        value = self.coordinator.data.get(state_key)
        
        if value is None:
            return None
        
        # Handle flow info status (0: off, 2: on)
        if state_key.startswith("flowInfo"):
            return value == 2
        
        # Handle boolean values
        return bool(value)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if self.is_on:
            return self._switch_def.get("icon_on")
        return self._switch_def.get("icon_off")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._send_command(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._send_command(False)

    async def _send_command(self, state: bool) -> None:
        """Send command to device."""
        command_key = self._switch_def["command_key"]
        device_sn = self.coordinator.device_sn
        
        # Standard handling for all switches
        params = {
            command_key: state
        }
        
        # Build command payload according to Delta Pro 3 API format
        payload = {
            "sn": device_sn,
            "cmdId": 17,
            "dirDest": 1,
            "dirSrc": 1,
            "cmdFunc": 254,
            "dest": 2,
            "needAck": True,
            "params": params
        }
        
        try:
            await self.coordinator.api_client.set_device_quota(
                device_sn=device_sn,
                cmd_code=payload,
            )
            # Wait 2 seconds for device to apply changes, then refresh
            await asyncio.sleep(2)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set %s to %s: %s",
                self._switch_key,
                state,
                err
            )
            raise
