"""MQTT client for EcoFlow devices.

This module provides MQTT connectivity for real-time updates from EcoFlow devices.
Based on EcoFlow Developer API MQTT documentation.

EcoFlow MQTT Protocol:
- Broker: mqtt.ecoflow.com:8883 (TLS)
- Protocol: MQTT v3.1.1
- Authentication: Username/Password (EcoFlow account credentials)
- Topics:
  - /open/{certificateAccount}/{sn}/quota - Device quota/status updates
  - /open/{certificateAccount}/{sn}/status - Device online/offline status
  - /open/{certificateAccount}/{sn}/set - Send commands to device
  - /open/{certificateAccount}/{sn}/set_reply - Command response from device

Note: certificateAccount is typically the user_id or username from EcoFlow account.
"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from typing import Any, Callable

import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

# EcoFlow MQTT Configuration
MQTT_BROKER = "mqtt.ecoflow.com"
MQTT_PORT = 8883
MQTT_KEEPALIVE = 60
MQTT_PROTOCOL = mqtt.MQTTv311


class EcoFlowMQTTClient:
    """EcoFlow MQTT client for real-time device updates."""

    def __init__(
        self,
        username: str,
        password: str,
        device_sn: str,
        on_message_callback: Callable[[dict[str, Any]], None] | None = None,
        on_status_callback: Callable[[bool], None] | None = None,
        certificate_account: str | None = None,
    ) -> None:
        """Initialize MQTT client.

        Args:
            username: EcoFlow account username/email (for MQTT authentication)
            password: EcoFlow account password (for MQTT authentication)
            device_sn: Device serial number
            on_message_callback: Callback function for received messages
            on_status_callback: Callback function for connection status changes (True=connected)
            certificate_account: Certificate account/user_id for topics (if None, uses username)
        """
        self.username = username
        self.password = password
        self.device_sn = device_sn
        self.on_message_callback = on_message_callback
        self.on_status_callback = on_status_callback

        self._client: mqtt.Client | None = None
        self._connected = False
        self._reconnect_task: asyncio.Task | None = None
        
        # MQTT topics (correct format: /open/${certificateAccount}/${sn}/...)
        # certificateAccount is typically the user_id (not email)
        # If not provided, try using username (but this might not work)
        self._certificate_account = certificate_account or username
        self._quota_topic = f"/open/{self._certificate_account}/{device_sn}/quota"
        self._status_topic = f"/open/{self._certificate_account}/{device_sn}/status"
        self._set_topic = f"/open/{self._certificate_account}/{device_sn}/set"
        self._set_reply_topic = f"/open/{self._certificate_account}/{device_sn}/set_reply"
        
    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected

    async def async_connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create MQTT client
            self._client = mqtt.Client(
                client_id=f"ha_ecoflow_{self.device_sn}",
                protocol=MQTT_PROTOCOL,
            )
            
            # Set credentials
            self._client.username_pw_set(self.username, self.password)
            
            # Configure TLS - run in executor to avoid blocking the event loop
            # ssl.create_default_context() loads certificates from disk which is blocking I/O
            def create_ssl_context():
                """Create SSL context (blocking operation)."""
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                return context
            
            loop = asyncio.get_event_loop()
            ssl_context = await loop.run_in_executor(None, create_ssl_context)
            self._client.tls_set_context(ssl_context)
            
            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            # Connect to broker
            
            # Use loop_start() for async operation
            self._client.connect_async(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self._client.loop_start()
            
            # Wait for connection (with timeout)
            for _ in range(10):  # 10 seconds timeout
                if self._connected:
                    return True
                await asyncio.sleep(1)
            
            _LOGGER.error("MQTT connection timeout for device %s", self.device_sn)
            return False
            
        except Exception as err:
            _LOGGER.error("Failed to connect to MQTT broker: %s", err)
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
            
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            
        self._connected = False
        _LOGGER.info("Disconnected from MQTT broker for device %s", self.device_sn)

    async def async_publish_command(self, command: dict[str, Any]) -> bool:
        """Publish command to device via MQTT set topic.

        Ensures the payload has required MQTT fields (id, version) that
        distinguish MQTT SET format from REST API format.

        Args:
            command: Command payload (REST or MQTT format)

        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot publish command: MQTT not connected")
            return False

        try:
            # Ensure MQTT-required fields are present
            mqtt_command = dict(command)
            if "id" not in mqtt_command:
                mqtt_command["id"] = int(time.time() * 1000)
            if "version" not in mqtt_command:
                mqtt_command["version"] = "1.0"

            # Delta Pro (original) MQTT format requires operateType and timestamp
            # Detect by checking for cmdSet inside params (Delta Pro format)
            params = mqtt_command.get("params", {})
            if isinstance(params, dict) and "cmdSet" in params:
                if "operateType" not in mqtt_command:
                    mqtt_command["operateType"] = "TCP"
                if "timestamp" not in mqtt_command:
                    mqtt_command["timestamp"] = int(time.time() * 1000)

            payload = json.dumps(mqtt_command)
            _LOGGER.debug(
                "MQTT publish to %s: %s",
                self._set_topic.split("/")[-2][-4:],  # last 4 chars of SN
                payload[:200],
            )
            result = self._client.publish(self._set_topic, payload, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                _LOGGER.error("Failed to publish command: rc=%s", result.rc)
                return False

        except Exception as err:
            _LOGGER.error("Error publishing command: %s", err)
            return False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict[str, Any],
        rc: int,
    ) -> None:
        """Handle MQTT connection."""
        # MQTT return codes: 0=success, 1=protocol version, 2=client ID, 3=server unavailable,
        # 4=bad credentials, 5=not authorized
        error_messages = {
            0: "Connection successful",
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized - check credentials",
        }

        if rc == 0:
            self._connected = True
            is_reconnect = flags.get("session present", False)
            _LOGGER.info(
                "✅ MQTT %s for device %s (certificateAccount=%s)",
                "reconnected" if is_reconnect else "connected",
                self.device_sn[-4:],
                self._certificate_account[:20] + "..." if len(self._certificate_account) > 20 else self._certificate_account,
            )

            # Subscribe to topics
            client.subscribe(self._quota_topic, qos=1)
            client.subscribe(self._status_topic, qos=1)
            client.subscribe(self._set_reply_topic, qos=1)
            _LOGGER.debug("Subscribed to MQTT topics: %s, %s, %s", self._quota_topic, self._status_topic, self._set_reply_topic)

            # Notify status callback
            if self.on_status_callback:
                self.on_status_callback(True)
        else:
            self._connected = False
            error_msg = error_messages.get(rc, f"Unknown error (code {rc})")
            _LOGGER.error(
                "❌ MQTT connection failed for device %s: %s (code %d)",
                self.device_sn[-4:],
                error_msg,
                rc
            )
            _LOGGER.error(
                "MQTT Troubleshooting:\n"
                "1. certificateAccount from API: %s\n"
                "2. Check if this is a user_id or email - should be a numeric ID\n"
                "3. Topics: quota=%s\n"
                "4. If error persists, try disabling and re-enabling MQTT in Options",
                self._certificate_account,
                self._quota_topic,
            )

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """Handle MQTT disconnection."""
        self._connected = False

        # MQTT disconnect reason codes
        disconnect_reasons = {
            0: "Normal disconnection",
            1: "Unexpected disconnection",
            5: "Not authorized",
            7: "Keep-alive timeout",
        }
        reason = disconnect_reasons.get(rc, f"Unknown (code {rc})")

        if rc != 0:
            _LOGGER.warning(
                "⚠️ MQTT disconnected for device %s: %s. Paho will auto-reconnect.",
                self.device_sn[-4:],
                reason
            )
        else:
            _LOGGER.info("Disconnected from MQTT broker for device %s", self.device_sn[-4:])

        # Notify status callback
        if self.on_status_callback:
            self.on_status_callback(False)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle received MQTT message."""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Handle different topic types
            if msg.topic == self._quota_topic:
                # Quota topic: payload can be direct data, wrapped in "params", or "param" (Powerstream)
                if "params" in payload:
                    quota_data = payload["params"]
                elif "param" in payload:
                    # Powerstream format: wrap in 20_1 to match HTTP GetAllQuotaResponse structure
                    quota_data = {"20_1": payload["param"]}
                else:
                    quota_data = payload
                
                if self.on_message_callback:
                    self.on_message_callback(quota_data)
                    
            elif msg.topic == self._status_topic:
                # Status topic: payload has "params.status" (0=offline, 1=online)
                if "params" in payload and "status" in payload["params"]:
                    status = payload["params"]["status"]
                    _LOGGER.info("Device %s status: %s", self.device_sn, "online" if status == 1 else "offline")
                    
            elif msg.topic == self._set_reply_topic:
                # Set reply formats by device type:
                #   Delta Pro 3:    {"data": {"configOk": true, ...}, "id": 123}
                #   Delta 2/Plug:   {"data": {"ack": 0}, "id": 123}
                #   Delta Pro Ultra: {"data": {"result": 0}, "id": 123}
                reply_data = payload.get("data", {})
                config_ok = reply_data.get("configOk")
                ack = reply_data.get("ack")
                result = reply_data.get("result")
                reply_id = payload.get("id")

                if config_ok is True or ack == 0 or result == 0:
                    _LOGGER.debug("Command reply OK for %s (id=%s): %s", self.device_sn[-4:], reply_id, reply_data)
                else:
                    _LOGGER.warning("Command reply for %s (id=%s): %s", self.device_sn[-4:], reply_id, payload)
                
            else:
                # Unknown topic
                if self.on_message_callback:
                    self.on_message_callback(payload)
                
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to decode MQTT message: %s", err)
        except Exception as err:
            _LOGGER.error("Error handling MQTT message: %s", err)

