"""MQTT client for EcoFlow devices.

This module provides MQTT connectivity for real-time updates from EcoFlow devices.
Based on research from tolwi/hassio-ecoflow-cloud integration.

EcoFlow MQTT Protocol:
- Broker: mqtt.ecoflow.com:8883 (TLS)
- Protocol: MQTT over WebSocket
- Authentication: Username/Password (from EcoFlow account)
- Topics: /app/{user_id}/{device_sn}/thing/property/set (commands)
          /app/device/property/{device_sn} (status updates)
"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
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
    ) -> None:
        """Initialize MQTT client.
        
        Args:
            username: EcoFlow account username/email
            password: EcoFlow account password
            device_sn: Device serial number
            on_message_callback: Callback function for received messages
        """
        self.username = username
        self.password = password
        self.device_sn = device_sn
        self.on_message_callback = on_message_callback
        
        self._client: mqtt.Client | None = None
        self._connected = False
        self._reconnect_task: asyncio.Task | None = None
        
        # MQTT topics
        self._status_topic = f"/app/device/property/{device_sn}"
        self._command_topic = f"/app/{username}/{device_sn}/thing/property/set"
        
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
            
            # Configure TLS
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self._client.tls_set_context(ssl_context)
            
            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
            # Connect to broker
            _LOGGER.info(
                "Connecting to MQTT broker %s:%d for device %s",
                MQTT_BROKER,
                MQTT_PORT,
                self.device_sn
            )
            
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
        """Publish command to device.
        
        Args:
            command: Command payload
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected or not self._client:
            _LOGGER.warning("Cannot publish command: MQTT not connected")
            return False
            
        try:
            payload = json.dumps(command)
            result = self._client.publish(self._command_topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                _LOGGER.debug("Published command to %s: %s", self._command_topic, payload)
                return True
            else:
                _LOGGER.error("Failed to publish command: %s", result.rc)
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
        if rc == 0:
            self._connected = True
            _LOGGER.info("Connected to MQTT broker for device %s", self.device_sn)
            
            # Subscribe to device status topic
            client.subscribe(self._status_topic, qos=1)
            _LOGGER.info("Subscribed to topic: %s", self._status_topic)
        else:
            self._connected = False
            _LOGGER.error("MQTT connection failed with code %d", rc)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """Handle MQTT disconnection."""
        self._connected = False
        
        if rc != 0:
            _LOGGER.warning(
                "Unexpected MQTT disconnection (code %d) for device %s. Will auto-reconnect.",
                rc,
                self.device_sn
            )
        else:
            _LOGGER.info("Disconnected from MQTT broker for device %s", self.device_sn)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle received MQTT message."""
        try:
            payload = json.loads(msg.payload.decode())
            _LOGGER.debug("Received MQTT message from %s: %s", msg.topic, payload)
            
            # Call callback if set
            if self.on_message_callback:
                self.on_message_callback(payload)
                
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to decode MQTT message: %s", err)
        except Exception as err:
            _LOGGER.error("Error handling MQTT message: %s", err)

