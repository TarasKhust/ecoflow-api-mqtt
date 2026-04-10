"""Coordinator for EcoFlow River 3 Plus using app-authenticated MQTT polling."""
from __future__ import annotations

import asyncio
import logging
import ssl
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import EcoFlowApiClient
from .const import DEVICE_TYPE_RIVER3PLUS
from .coordinator import EcoFlowDataCoordinator
from .devices.river3plus import River3PlusDevice

_LOGGER = logging.getLogger(__name__)


def _encode_varint(value: int) -> bytes:
    """Encode a protobuf varint."""
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _field_varint(field_number: int, value: int) -> bytes:
    """Build a protobuf varint field."""
    return _encode_varint((field_number << 3) | 0) + _encode_varint(value)


def _field_string(field_number: int, value: str) -> bytes:
    """Build a protobuf string field."""
    payload = value.encode("utf-8")
    return (
        _encode_varint((field_number << 3) | 2)
        + _encode_varint(len(payload))
        + payload
    )


def _field_message(field_number: int, payload: bytes) -> bytes:
    """Build a protobuf nested-message field."""
    return (
        _encode_varint((field_number << 3) | 2)
        + _encode_varint(len(payload))
        + payload
    )


def _build_latest_quotas_request() -> bytes:
    """Build the River 3 Plus `thing/property/get` protobuf request.

    This matches the app-originated request shape used by working
    third-party integrations: `setMessage { header { src=32, dest=32,
    seq=<now>, from='ios' } }`.
    """
    header = b"".join(
        [
            _field_varint(2, 32),
            _field_varint(3, 32),
            _field_varint(14, int(time.time() * 1000)),
            _field_string(23, "ios"),
        ]
    )
    return _field_message(1, header)


class River3PlusCoordinator(EcoFlowDataCoordinator):
    """MQTT-only coordinator for River 3 Plus.

    River 3 Plus does not expose quotas through the Developer REST API. It also
    does not reliably publish passive telemetry over MQTT with developer-issued
    certs. The working path is:

    1. Log in with EcoFlow app credentials.
    2. Fetch app-authenticated MQTT certs.
    3. Publish a protobuf `thing/property/get` request.
    4. Decode the protobuf `thing/property/get_reply` payload.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: EcoFlowApiClient,
        device_sn: str,
        update_interval: int = 15,
        config_entry: ConfigEntry | None = None,
        app_username: str | None = None,
        app_password: str | None = None,
    ) -> None:
        """Initialise coordinator."""
        super().__init__(
            hass=hass,
            client=client,
            device_sn=device_sn,
            device_type=DEVICE_TYPE_RIVER3PLUS,
            update_interval=update_interval,
            config_entry=config_entry,
        )
        self._app_username = app_username
        self._app_password = app_password
        self._device = River3PlusDevice(device_sn)
        self._mqtt_data: dict[str, Any] = {}
        self._paho_client: mqtt.Client | None = None
        self._mqtt_connected = False
        self._user_id: str | None = None
        self._connected_event = asyncio.Event()
        self._reply_event: asyncio.Event | None = None

    def _raise_read_only(self) -> None:
        """Reject command paths for River 3 Plus."""
        raise RuntimeError(
            f"River 3 Plus [{self.device_sn[-4:]}] is read-only in this integration"
        )

    async def async_setup(self) -> bool:
        """Fetch app MQTT credentials and connect the MQTT client."""
        if not self._app_username or not self._app_password:
            _LOGGER.error(
                "River 3 Plus [%s]: EcoFlow app credentials are required",
                self.device_sn[-4:],
            )
            return False

        try:
            creds = await self.client.get_app_mqtt_credentials(
                self._app_username, self._app_password
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error(
                "River 3 Plus [%s]: cannot obtain app MQTT credentials: %s",
                self.device_sn[-4:],
                err,
            )
            return False

        self._user_id = creds["userId"]
        mqtt_url = creds.get("url", "mqtt.ecoflow.com")
        mqtt_port = int(creds.get("port", 8883))
        username = creds["certificateAccount"]
        password = creds["certificatePassword"]
        client_id = f"ANDROID_{str(uuid.uuid4()).upper()}_{self._user_id}"

        await self.hass.async_add_executor_job(
            self._setup_paho_mqtt,
            client_id,
            username,
            password,
            mqtt_url,
            mqtt_port,
        )

        self.hass.bus.async_listen_once("homeassistant_stop", self._async_handle_stop)

        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=15)
        except asyncio.TimeoutError:
            _LOGGER.error(
                "River 3 Plus [%s]: timed out connecting to MQTT broker",
                self.device_sn[-4:],
            )
            return False

        return self._mqtt_connected

    async def _async_handle_stop(self, _event: Any) -> None:
        """Shut down gracefully on Home Assistant stop."""
        await self.async_shutdown()

    async def async_shutdown(self) -> None:
        """Disconnect the MQTT client."""
        if self._paho_client:
            await self.hass.async_add_executor_job(self._disconnect_paho)
            self._paho_client = None
        self._mqtt_connected = False
        self._connected_event.clear()

    async def async_send_command(self, command: dict) -> bool:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_ac_charging_power(self, power: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_max_charge_level(self, level: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_min_discharge_level(self, level: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_ac_output(self, enabled: bool) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_dc_output(self, enabled: bool) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_12v_dc_output(self, enabled: bool) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_beep(self, enabled: bool) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_x_boost(self, enabled: bool) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_ac_standby_time(self, minutes: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_dc_standby_time(self, minutes: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def async_set_lcd_standby_time(self, seconds: int) -> None:
        """Block command writes for River 3 Plus."""
        self._raise_read_only()

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll River 3 Plus state through MQTT `thing/property/get`."""
        if not self._mqtt_connected or not self._paho_client or not self._user_id:
            raise UpdateFailed("River 3 Plus MQTT is not connected")

        self._reply_event = asyncio.Event()
        await self.hass.async_add_executor_job(self._publish_latest_quotas_request)

        try:
            await asyncio.wait_for(self._reply_event.wait(), timeout=15)
        except asyncio.TimeoutError as err:
            if self._mqtt_data:
                return dict(self._mqtt_data)
            raise UpdateFailed("Timed out waiting for River 3 Plus MQTT reply") from err

        return dict(self._mqtt_data)

    def _setup_paho_mqtt(
        self,
        client_id: str,
        username: str,
        password: str,
        url: str,
        port: int,
    ) -> None:
        """Create and connect the paho-mqtt client."""
        self._paho_client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )
        self._paho_client.username_pw_set(username, password)

        ssl_ctx = ssl.create_default_context()
        self._paho_client.tls_set_context(ssl_ctx)

        self._paho_client.on_connect = self._on_paho_connect
        self._paho_client.on_disconnect = self._on_paho_disconnect
        self._paho_client.on_message = self._on_paho_message

        self._paho_client.connect_async(url, port, keepalive=60)
        self._paho_client.loop_start()

    def _disconnect_paho(self) -> None:
        """Disconnect paho-mqtt client."""
        if self._paho_client:
            self._paho_client.loop_stop()
            self._paho_client.disconnect()

    def _publish_latest_quotas_request(self) -> None:
        """Publish the protobuf latest-quotas request."""
        if not self._paho_client or not self._user_id:
            return

        topic = f"/app/{self._user_id}/{self.device_sn}/thing/property/get"
        payload = _build_latest_quotas_request()
        self._paho_client.publish(topic, payload, qos=1)

    def _on_paho_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict[str, Any],
        rc: int,
    ) -> None:
        """Handle MQTT connection state."""
        self._mqtt_connected = rc == 0
        if rc != 0 or not self._user_id:
            _LOGGER.error(
                "River 3 Plus [%s]: MQTT connection failed (rc=%s)",
                self.device_sn[-4:],
                rc,
            )
            return

        client.subscribe(
            [
                (f"/app/{self._user_id}/{self.device_sn}/thing/property/get_reply", 1),
                (f"/app/device/property/{self.device_sn}", 1),
            ]
        )
        self.hass.loop.call_soon_threadsafe(self._connected_event.set)

    def _on_paho_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """Handle MQTT disconnects."""
        self._mqtt_connected = False
        self.hass.loop.call_soon_threadsafe(self._connected_event.clear)

    def _on_paho_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Decode protobuf replies from the River 3 Plus."""
        try:
            decoded = self._device.decode_packet(bytes(msg.payload))
            if not decoded:
                return

            self._mqtt_data.update(decoded)
            snapshot = dict(self._mqtt_data)
            self.hass.loop.call_soon_threadsafe(self._async_handle_decoded_update, snapshot)
        except RuntimeError:
            pass
        except Exception as err:  # noqa: BLE001
            _LOGGER.error(
                "River 3 Plus [%s]: error processing MQTT message: %s",
                self.device_sn[-4:],
                err,
            )

    def _async_handle_decoded_update(self, snapshot: dict[str, Any]) -> None:
        """Push decoded data into Home Assistant from the main event loop."""
        self.async_set_updated_data(snapshot)
        if self._reply_event is not None and not self._reply_event.is_set():
            self._reply_event.set()
