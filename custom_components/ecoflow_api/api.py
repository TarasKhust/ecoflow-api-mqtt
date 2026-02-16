"""EcoFlow API client."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import random
import string
import time

import aiohttp

from .const import API_BASE_URL_EU, API_BASE_URL_US, API_TIMEOUT, REGION_EU, JsonVal

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
        return "".join(random.choices(string.digits, k=length))  # noqa: S311

    def _flatten_params(self, params: dict[str, JsonVal], parent_key: str = "") -> dict[str, str]:
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
                        items[f"{new_key}[{i}]"] = str(item).lower() if isinstance(item, bool) else str(item)
            else:
                # Convert boolean to lowercase string (true/false)
                items[new_key] = str(value).lower() if isinstance(value, bool) else str(value)
        return items

    def _sort_and_concat_params(self, params: dict[str, JsonVal]) -> str:
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
        params: dict[str, JsonVal] | None = None,
        data: dict[str, JsonVal] | None = None,
    ) -> dict[str, JsonVal]:
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
        sign_params = (params if method == "GET" else data) or {}
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
                    async with self._session.post(url, headers=headers, json=data) as response:
                        return await self._handle_response(response)
                elif method == "PUT":
                    async with self._session.put(url, headers=headers, json=data) as response:
                        return await self._handle_response(response)
                elif method == "DELETE":
                    async with self._session.delete(url, headers=headers, json=data) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

        except TimeoutError as err:
            raise EcoFlowConnectionError(f"Timeout connecting to EcoFlow API: {err}") from err
        except aiohttp.ClientError as err:
            raise EcoFlowConnectionError(f"Error connecting to EcoFlow API: {err}") from err

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, JsonVal]:
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
            raise EcoFlowApiError(f"API request failed with status {response.status}: {text}")

        try:
            result: dict[str, JsonVal] = await response.json()  # type: ignore[assignment]
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

        data = result.get("data", result)
        return data if isinstance(data, dict) else result

    async def get_mqtt_credentials(self) -> dict[str, JsonVal]:
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

        # Log full response for debugging (mask password)
        cert_account = str(result.get("certificateAccount", "N/A"))
        cert_password = str(result.get("certificatePassword", ""))
        masked_password = f"{cert_password[:4]}...{cert_password[-4:]}" if len(cert_password) > 8 else "***"

        _LOGGER.info(
            "MQTT credentials from API: url=%s, port=%s, certificateAccount=%s, password=%s",
            result.get("url", "N/A"),
            result.get("port", "N/A"),
            cert_account,
            masked_password,
        )

        return result

    async def get_device_list(self) -> list[dict[str, JsonVal]]:
        """Get list of all devices associated with the account.

        Returns:
            List of device information dictionaries
        """
        result = await self._request("GET", "/iot-open/sign/device/list")
        return result if isinstance(result, list) else []

    async def get_device_quota(self, device_sn: str) -> dict[str, JsonVal]:
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
        cmd_code: dict[str, JsonVal] | str,
        params: dict[str, JsonVal] | None = None,
    ) -> dict[str, JsonVal]:
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

        _LOGGER.debug("SET device quota: PUT payload=%s", data)

        result = await self._request(
            "PUT",
            "/iot-open/sign/device/quota",
            data=data,
        )

        _LOGGER.debug("SET device quota: response=%s", result)
        return result

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
