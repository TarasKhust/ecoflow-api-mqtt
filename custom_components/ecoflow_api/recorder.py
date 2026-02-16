"""Recorder configuration for EcoFlow API integration.

Excludes technical attributes from being recorded in Home Assistant database
to reduce database size and improve performance.
"""

from homeassistant.core import HomeAssistant, callback


@callback
def exclude_attributes(hass: HomeAssistant) -> set[str]:
    """Return attributes that should be excluded from recorder.

    These attributes are technical/diagnostic and don't need to be stored
    in the database history.
    """
    return {
        # Existing
        "mqtt_connected",
        "mqtt_connection_mode",
        "last_update_success",
        "last_update_time",
        "update_interval",
        "device_info",
        "attribution",
        # Additional (from ecoflow-cloud)
        "status_request_count",
        "status_last_update",
        "data_last_update",
        "status_phase",
        "quota_requests",
        "reconnects",
        # Diagnostic
        "rest_requests",
        "mqtt_messages",
        "set_commands",
        "set_replies",
    }
