"""EcoFlow API client."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import random
import string
import time
from typing import Any

import aiohttp

from .const import API_BASE_URL_EU, API_BASE_URL_US, API_TIMEOUT, REGION_EU

_LOGGER = logging.getLogger(__name__)


class EcoFlowApiError(Exception):
    """Exception for EcoFlow API errors."""


class EcoFlowAuthError(EcoFlowApiError):
    """Exception for authentication errors."""


class EcoFlowConnectionError(EcoFlowApiError):
    """Exception for connection errors."""


class EcoFlowApiClient:
    """EcoFlow API client using official Developer API.

    Documentation: https://developer-eu.ecoflow.com/us/document/introduction
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        session: aiohttp.ClientSession,
        region: str = REGION_EU,
    ) -> None:
        """Initialize the API client.

        Args:
            access_key: EcoFlow Developer API access key
            secret_key: EcoFlow Developer API secret key
            session: aiohttp client session
            region: API region (eu or us)
        """
        self._access_key = access_key
        self._secret_key = secret_key
        self._session = session
        self._region = region
        self._base_url = API_BASE_URL_US if region != REGION_EU else API_BASE_URL_EU

    def _generate_nonce(self, length: int = 6) -> str:
        """Generate a random 6-digit nonce string."""
        return "".join(random.choices(string.digits, k=length))

    def _flatten_params(
        self, params: dict[str, Any], parent_key: str = ""
    ) -> dict[str, str]:
        """Flatten nested dictionary for signature generation."""
        items = {}
        for key, value in params.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                items.update(self._flatten_params(value, new_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.update(self._flatten_params(item, f"{new_key}[{i}]"))
                    else:
                        items[f"{new_key}[{i}]"] = (
                            str(item).lower() if isinstance(item, bool) else str(item)
                        )
            else:
                # Convert boolean to lowercase string (true/false)
                items[new_key] = (
                    str(value).lower() if isinstance(value, bool) else str(value)
                )
        return items

    def _sort_and_concat_params(self, params: dict[str, Any]) -> str:
        """Sort and concatenate parameters into query string.

        Args:
            params: Parameters to concatenate

        Returns:
            Query string like "key1=value1&key2=value2"
        """
        if not params:
            return ""

        # Flatten nested params
        flat_params = self._flatten_params(params)

        # Sort by key
        sorted_items = sorted(flat_params.items())

        # Create query string
        return "&".join(f"{key}={value}" for key, value in sorted_items)

    def _get_headers(
        self,
        params_str: str,
        timestamp: str,
        nonce: str,
        include_content_type: bool = False,
    ) -> dict[str, str]:
        """Get request headers with authentication.

        Args:
            params_str: Pre-formatted query string with flattened parameters
            timestamp: Timestamp string
            nonce: Nonce string
            include_content_type: Whether to include Content-Type header

        Returns:
            Headers dictionary

        Note:
            Signature generation:
            - GET: flatten query params + auth params (accessKey, nonce, timestamp)
            - PUT/POST: flatten JSON body params + auth params
        """
        # Generate signature: flattened params + auth parameters
        auth_str = f"accessKey={self._access_key}&nonce={nonce}&timestamp={timestamp}"
        if params_str:
            # Include params in signature (query params for GET, body params for PUT/POST)
            sign_str = f"{params_str}&{auth_str}"
        else:
            # No params: signature only from auth params
            sign_str = auth_str

        signature = hmac.new(
            self._secret_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "accessKey": self._access_key,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": signature,
        }

        # Only add Content-Type for POST/PUT with JSON body
        if include_content_type:
            headers["Content-Type"] = "application/json;charset=UTF-8"

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] = None,
        data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Make API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters for GET requests
            data: JSON body for POST/PUT requests

        Returns:
            API response data

        Raises:
            EcoFlowApiError: If API returns an error
            EcoFlowConnectionError: If connection fails
        """
        # Generate timestamp and nonce
        timestamp = str(int(time.time() * 1000))
        nonce = self._generate_nonce()

        # For GET requests, params go in query string and signature
        # For POST/PUT, params go in body and signature includes flattened body params
        sign_params = params if method == "GET" else (data or {})
        params_str = self._sort_and_concat_params(sign_params)

        # Get authenticated headers
        # Content-Type only for POST/PUT with JSON body
        include_content_type = method in ("POST", "PUT") and data is not None
        headers = self._get_headers(params_str, timestamp, nonce, include_content_type)

        # Build URL with query string for GET
        if method == "GET" and params_str:
            url = f"{self._base_url}{endpoint}?{params_str}"
        else:
            url = f"{self._base_url}{endpoint}"

        try:
            async with asyncio.timeout(API_TIMEOUT):
                if method == "GET":
                    async with self._session.get(url, headers=headers) as response:
                        return await self._handle_response(response)
                elif method == "POST":
                    async with self._session.post(
                        url, headers=headers, json=data
                    ) as response:
                        return await self._handle_response(response)
                elif method == "PUT":
                    async with self._session.put(
                        url, headers=headers, json=data
                    ) as response:
                        return await self._handle_response(response)
                elif method == "DELETE":
                    async with self._session.delete(
                        url, headers=headers, json=data
                    ) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

        except asyncio.TimeoutError as err:
            raise EcoFlowConnectionError(
                f"Timeout connecting to EcoFlow API: {err}"
            ) from err
        except aiohttp.ClientError as err:
            raise EcoFlowConnectionError(
                f"Error connecting to EcoFlow API: {err}"
            ) from err

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> dict[str, Any]:
        """Handle API response.

        Args:
            response: aiohttp response object

        Returns:
            Parsed response data

        Raises:
            EcoFlowAuthError: If authentication fails
            EcoFlowApiError: If API returns an error
        """
        text = await response.text()

        if response.status == 401:
            raise EcoFlowAuthError("Authentication failed - check your API credentials")

        if response.status != 200:
            raise EcoFlowApiError(
                f"API request failed with status {response.status}: {text}"
            )

        try:
            result = await response.json()
        except Exception as err:
            raise EcoFlowApiError(f"Failed to parse API response: {err}") from err

        # Check for API-level errors
        code = result.get("code")
        if code not in ("0", 0, "200", 200, None):
            message = result.get("message", "Unknown error")
            
            # Special handling for error 1006 - device not allowed
            if code == 1006 or code == "1006":
                detailed_message = (
                    f"API error (code {code}): {message}\n\n"
                    "This error typically means:\n"
                    "1. The device is not properly bound to your EcoFlow Developer account\n"
                    "2. EcoFlow hasn't enabled API access for this device model yet\n"
                    "3. The device serial number might be incorrect\n\n"
                    "Troubleshooting steps:\n"
                                "- Verify the device is bound to your account in the EcoFlow app\n"
                                "- Check that you're using the correct device serial number\n"
                                "- Try regenerating your API credentials in the Developer Portal\n"
                                "- Contact EcoFlow support to enable API access for your device\n"
                                "- Note: River 3 and River 3 Plus are not supported by EcoFlow REST API (error 1006)"
                )
                raise EcoFlowApiError(detailed_message)
            
            raise EcoFlowApiError(f"API error (code {code}): {message}")

        return result.get("data", result)

    async def get_mqtt_credentials(self) -> dict[str, Any]:
        """Get MQTT credentials (certificateAccount and certificatePassword).

        Returns:
            Dictionary with MQTT credentials: {
                "url": "mqtt.ecoflow.com",
                "port": 8883,
                "certificateAccount": "...",
                "certificatePassword": "..."
            }
        """
        result = await self._request("GET", "/iot-open/sign/certification")
        _LOGGER.info(
            "Received MQTT credentials: certificateAccount=%s",
            result.get("certificateAccount", "N/A"),
        )
        return result

    async def get_device_list(self) -> list[dict[str, Any]]:
        """Get list of all devices associated with the account.

        Returns:
            List of device information dictionaries
        """
        result = await self._request("GET", "/iot-open/sign/device/list")
        return result if isinstance(result, list) else []

    async def get_device_quota(self, device_sn: str) -> dict[str, Any]:
        """Get all device quotas/status.

        Args:
            device_sn: Device serial number

        Returns:
            Device status and settings
        """
        return await self._request(
            "GET",
            "/iot-open/sign/device/quota/all",
            params={"sn": device_sn},
        )

    async def set_device_quota(
        self,
        device_sn: str,
        cmd_code: dict[str, Any] | str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set device quota/parameter.

        Args:
            device_sn: Device serial number
            cmd_code: Full command payload (dict) or command code string (legacy)
            params: Command parameters (only used if cmd_code is string)

        Returns:
            API response
        """
        # Support both new format (full payload) and legacy format (cmd_code + params)
        if isinstance(cmd_code, dict):
            # New format: cmd_code is the full payload
            data = cmd_code
        else:
            # Legacy format: build payload from cmd_code and params
            data = {
                "sn": device_sn,
                "cmdCode": cmd_code,
                "params": params or {},
            }

        return await self._request(
            "PUT",
            "/iot-open/sign/device/quota",
            data=data,
        )

    async def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection is successful
        """
        try:
            await self.get_device_list()
            return True
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    # Delta Pro 3 specific methods
    # Documentation: https://developer-eu.ecoflow.com/us/document/deltaPro3

    async def set_ac_charging_power(
        self, device_sn: str, power: int, pause: bool = False
    ) -> dict[str, Any]:
        """Set AC charging power for Delta Pro 3.

        Args:
            device_sn: Device serial number
            power: Charging power in watts (200-3000)
            pause: Whether to pause charging

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_AC_CHARGE_SPEED

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_AC_CHARGE_SPEED,
            {
                "chgPauseFlag": 1 if pause else 0,
                "acChgPower": max(200, min(3000, power)),
            },
        )

    async def set_charge_levels(
        self,
        device_sn: str,
        max_charge: int = None,
        min_discharge: int = None,
    ) -> dict[str, Any]:
        """Set charge/discharge levels for Delta Pro 3.

        Args:
            device_sn: Device serial number
            max_charge: Maximum charge level (50-100%)
            min_discharge: Minimum discharge level (0-30%)

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_CHARGE_LEVEL

        params = {}
        if max_charge is not None:
            params["maxChgSoc"] = max(50, min(100, max_charge))
        if min_discharge is not None:
            params["minDsgSoc"] = max(0, min(30, min_discharge))

        if not params:
            raise ValueError("At least one of max_charge or min_discharge must be set")

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_CHARGE_LEVEL,
            params,
        )

    async def set_ac_output(self, device_sn: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable AC output for Delta Pro 3.

        Args:
            device_sn: Device serial number
            enabled: Whether to enable AC output

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_AC_OUT

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_AC_OUT,
            {"acOutState": 1 if enabled else 0},
        )

    async def set_dc_output(self, device_sn: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable DC output for Delta Pro 3.

        Args:
            device_sn: Device serial number
            enabled: Whether to enable DC output

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_DC_OUT

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_DC_OUT,
            {"dcOutState": 1 if enabled else 0},
        )

    async def set_12v_dc_output(self, device_sn: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable 12V DC output for Delta Pro 3.

        Args:
            device_sn: Device serial number
            enabled: Whether to enable 12V DC output

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_12V_DC_OUT

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_12V_DC_OUT,
            {"dc12vOutState": 1 if enabled else 0},
        )

    async def set_beep(self, device_sn: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable beep for Delta Pro 3.

        Args:
            device_sn: Device serial number
            enabled: Whether to enable beep

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_BEEP

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_BEEP,
            {"beepState": 1 if enabled else 0},
        )

    async def set_x_boost(self, device_sn: str, enabled: bool) -> dict[str, Any]:
        """Enable/disable X-Boost for Delta Pro 3.

        Args:
            device_sn: Device serial number
            enabled: Whether to enable X-Boost

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_X_BOOST

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_X_BOOST,
            {"xBoostState": 1 if enabled else 0},
        )

    async def set_ac_standby_time(self, device_sn: str, minutes: int) -> dict[str, Any]:
        """Set AC standby time for Delta Pro 3.

        Args:
            device_sn: Device serial number
            minutes: Standby time in minutes (0 = never off)

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_AC_STANDBY_TIME

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_AC_STANDBY_TIME,
            {"acStandbyTime": minutes},
        )

    async def set_dc_standby_time(self, device_sn: str, minutes: int) -> dict[str, Any]:
        """Set DC standby time for Delta Pro 3.

        Args:
            device_sn: Device serial number
            minutes: Standby time in minutes (0 = never off)

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_DC_STANDBY_TIME

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_DC_STANDBY_TIME,
            {"dcStandbyTime": minutes},
        )

    async def set_lcd_standby_time(
        self, device_sn: str, seconds: int
    ) -> dict[str, Any]:
        """Set LCD/Screen standby time for Delta Pro 3.

        Args:
            device_sn: Device serial number
            seconds: Standby time in seconds (0 = never off)

        Returns:
            API response
        """
        from .const import CMD_DELTA_PRO_3_SET_LCD_STANDBY_TIME

        return await self.set_device_quota(
            device_sn,
            CMD_DELTA_PRO_3_SET_LCD_STANDBY_TIME,
            {"lcdOffTime": seconds},
        )
