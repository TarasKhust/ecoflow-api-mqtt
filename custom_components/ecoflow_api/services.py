"""Custom services for EcoFlow API integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import (
    DEVICE_TYPE_STREAM_ULTRA,
    DEVICE_TYPE_STREAM_ULTRA_X,
    DOMAIN,
)
from .coordinator import EcoFlowDataCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_BASE_LOAD_SCHEDULE = "set_base_load_schedule"

ATTR_DEVICE_SN = "device_sn"
ATTR_SCHEDULE = "schedule"
ATTR_START_MIN = "start_min"
ATTR_END_MIN = "end_min"
ATTR_LOAD_POWER = "load_power"

STREAM_BASE_LOAD_STATE_KEY = "dayResidentLoadList"
STREAM_BASE_LOAD_PARAM_KEY = "cfgDayResidentLoadList"
STREAM_BASE_LOAD_MIN_POWER = 0
STREAM_BASE_LOAD_MAX_POWER = 800
STREAM_BASE_LOAD_MINUTE_MIN = 0
STREAM_BASE_LOAD_MINUTE_MAX = 1440

STREAM_BASE_LOAD_DEVICE_TYPES = {
    DEVICE_TYPE_STREAM_ULTRA_X,
    DEVICE_TYPE_STREAM_ULTRA,
    "stream_ultra_x",
    "stream_ultra",
    "Stream Ultra X",
    "Stream Ultra",
}

_SCHEDULE_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_START_MIN): vol.All(
            vol.Coerce(int),
            vol.Range(min=STREAM_BASE_LOAD_MINUTE_MIN, max=STREAM_BASE_LOAD_MINUTE_MAX),
        ),
        vol.Required(ATTR_END_MIN): vol.All(
            vol.Coerce(int),
            vol.Range(min=STREAM_BASE_LOAD_MINUTE_MIN, max=STREAM_BASE_LOAD_MINUTE_MAX),
        ),
        vol.Required(ATTR_LOAD_POWER): vol.All(
            vol.Coerce(int),
            vol.Range(min=STREAM_BASE_LOAD_MIN_POWER, max=STREAM_BASE_LOAD_MAX_POWER),
        ),
    }
)


def _require_service_target(value: dict[str, Any]) -> dict[str, Any]:
    """Require exactly one target selector for a service call."""
    target_count = sum(
        1 for key in (ATTR_DEVICE_SN, CONF_DEVICE_ID) if value.get(key) is not None
    )
    if target_count != 1:
        raise vol.Invalid("expected exactly one of device_sn or device_id")
    return value


SET_BASE_LOAD_SCHEDULE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(ATTR_DEVICE_SN): cv.string,
            vol.Optional(CONF_DEVICE_ID): cv.string,
            vol.Required(ATTR_SCHEDULE): vol.All(
                cv.ensure_list,
                vol.Length(min=1),
                [_SCHEDULE_ENTRY_SCHEMA],
            ),
        }
    ),
    _require_service_target,
)


def _stream_base_load_payload(
    current_schedule: Any, schedule: list[dict[str, int]]
) -> dict[str, Any]:
    """Build a cfgDayResidentLoadList payload from service schedule data."""
    payload = dict(current_schedule) if isinstance(current_schedule, dict) else {}
    payload["load"] = [
        {
            "startMin": entry[ATTR_START_MIN],
            "endMin": entry[ATTR_END_MIN],
            "loadPower": entry[ATTR_LOAD_POWER],
        }
        for entry in schedule
    ]
    return payload


def _stream_base_load_command(
    device_sn: str, current_schedule: Any, schedule: list[dict[str, int]]
) -> dict[str, Any]:
    """Build the confirmed Stream command for resident-load schedules."""
    return {
        "sn": device_sn,
        "cmdId": 17,
        "cmdFunc": 254,
        "dirDest": 1,
        "dirSrc": 1,
        "dest": 2,
        "needAck": True,
        "params": {
            STREAM_BASE_LOAD_PARAM_KEY: _stream_base_load_payload(
                current_schedule, schedule
            )
        },
    }


def _coordinator_for_service_call(
    hass: HomeAssistant, call: ServiceCall
) -> EcoFlowDataCoordinator:
    """Return the configured coordinator targeted by a service call."""
    coordinators = hass.data.get(DOMAIN, {})

    device_sn = call.data.get(ATTR_DEVICE_SN)
    if device_sn is not None:
        for coordinator in coordinators.values():
            if coordinator.device_sn == device_sn:
                return coordinator
        raise HomeAssistantError(f"No EcoFlow device found with serial {device_sn}")

    device_id = call.data[CONF_DEVICE_ID]
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)
    if device_entry is None:
        raise HomeAssistantError(f"No EcoFlow device found with device_id {device_id}")

    for identifier_domain, identifier in device_entry.identifiers:
        if identifier_domain != DOMAIN:
            continue
        for coordinator in coordinators.values():
            if coordinator.device_sn == identifier:
                return coordinator

    raise HomeAssistantError(f"No EcoFlow config entry found for device_id {device_id}")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register EcoFlow API services."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_BASE_LOAD_SCHEDULE):
        return

    async def async_set_base_load_schedule(call: ServiceCall) -> None:
        coordinator = _coordinator_for_service_call(hass, call)
        if coordinator.device_type not in STREAM_BASE_LOAD_DEVICE_TYPES:
            raise HomeAssistantError(
                "Base-load schedules are only supported for Stream Ultra X "
                "or Stream Ultra devices"
            )

        schedule = call.data[ATTR_SCHEDULE]
        command = _stream_base_load_command(
            coordinator.device_sn,
            coordinator.data.get(STREAM_BASE_LOAD_STATE_KEY)
            if coordinator.data
            else None,
            schedule,
        )

        try:
            await coordinator.async_send_command(command)
            await asyncio.sleep(1)
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to set Stream base-load schedule for %s: %s",
                coordinator.device_sn,
                err,
            )
            raise HomeAssistantError(
                f"Failed to set Stream base-load schedule: {err}"
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BASE_LOAD_SCHEDULE,
        async_set_base_load_schedule,
        schema=SET_BASE_LOAD_SCHEDULE_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister EcoFlow API services when the last entry is unloaded."""
    if hass.data.get(DOMAIN):
        return

    if hass.services.has_service(DOMAIN, SERVICE_SET_BASE_LOAD_SCHEDULE):
        hass.services.async_remove(DOMAIN, SERVICE_SET_BASE_LOAD_SCHEDULE)
