"""Tests for EcoFlow API client."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ecoflow_api.api import (
    EcoFlowApiClient,
    EcoFlowApiError,
    EcoFlowAuthError,
    EcoFlowConnectionError,
)


def _make_mock_session():
    """Create a mock aiohttp session."""
    return MagicMock()


def _make_client(session=None, region="eu"):
    """Create an API client with mock session."""
    if session is None:
        session = _make_mock_session()
    return EcoFlowApiClient(
        access_key="test_access_key",
        secret_key="test_secret_key",
        session=session,
        region=region,
    )


class TestApiClientInit:
    """Test API client initialization."""

    def test_eu_region_url(self):
        client = _make_client(region="eu")
        assert client._base_url == "https://api-e.ecoflow.com"

    def test_us_region_url(self):
        client = _make_client(region="us")
        assert client._base_url == "https://api.ecoflow.com"

    def test_default_region_is_eu(self):
        session = _make_mock_session()
        client = EcoFlowApiClient("key", "secret", session)
        assert client._base_url == "https://api-e.ecoflow.com"


class TestNonceGeneration:
    """Test nonce generation."""

    def test_nonce_length(self):
        client = _make_client()
        nonce = client._generate_nonce()
        assert len(nonce) == 6

    def test_nonce_custom_length(self):
        client = _make_client()
        nonce = client._generate_nonce(length=10)
        assert len(nonce) == 10

    def test_nonce_is_digits(self):
        client = _make_client()
        nonce = client._generate_nonce()
        assert nonce.isdigit()

    def test_nonce_varies(self):
        client = _make_client()
        nonces = {client._generate_nonce() for _ in range(100)}
        # Should produce at least some variety (extremely unlikely to be all same)
        assert len(nonces) > 1


class TestParamFlattening:
    """Test _flatten_params for signature generation."""

    def test_flat_params(self):
        client = _make_client()
        result = client._flatten_params({"key1": "val1", "key2": 42})
        assert result == {"key1": "val1", "key2": "42"}

    def test_nested_params(self):
        client = _make_client()
        result = client._flatten_params({"parent": {"child": "value"}})
        assert result == {"parent.child": "value"}

    def test_boolean_lowercase(self):
        client = _make_client()
        result = client._flatten_params({"flag": True, "other": False})
        assert result == {"flag": "true", "other": "false"}

    def test_list_params(self):
        client = _make_client()
        result = client._flatten_params({"items": [1, 2, 3]})
        assert result == {"items[0]": "1", "items[1]": "2", "items[2]": "3"}

    def test_list_of_dicts(self):
        client = _make_client()
        result = client._flatten_params({"items": [{"a": 1}, {"b": 2}]})
        assert result == {"items[0].a": "1", "items[1].b": "2"}

    def test_empty_params(self):
        client = _make_client()
        result = client._flatten_params({})
        assert result == {}


class TestParamSorting:
    """Test _sort_and_concat_params."""

    def test_empty(self):
        client = _make_client()
        assert client._sort_and_concat_params({}) == ""

    def test_sorted_output(self):
        client = _make_client()
        result = client._sort_and_concat_params({"z": 1, "a": 2, "m": 3})
        assert result == "a=2&m=3&z=1"

    def test_boolean_handling(self):
        client = _make_client()
        result = client._sort_and_concat_params({"flag": True})
        assert result == "flag=true"


class TestSignatureGeneration:
    """Test HMAC signature generation."""

    def test_headers_contain_required_fields(self):
        client = _make_client()
        headers = client._get_headers("sn=TEST", "1234567890", "123456")
        assert "accessKey" in headers
        assert "timestamp" in headers
        assert "nonce" in headers
        assert "sign" in headers

    def test_signature_is_hex(self):
        client = _make_client()
        headers = client._get_headers("sn=TEST", "1234567890", "123456")
        sign = headers["sign"]
        # Should be hex string (SHA256 = 64 hex chars)
        assert len(sign) == 64
        assert all(c in "0123456789abcdef" for c in sign)

    def test_signature_reproducible(self):
        client = _make_client()
        h1 = client._get_headers("sn=TEST", "1234567890", "123456")
        h2 = client._get_headers("sn=TEST", "1234567890", "123456")
        assert h1["sign"] == h2["sign"]

    def test_signature_changes_with_params(self):
        client = _make_client()
        h1 = client._get_headers("sn=TEST1", "1234567890", "123456")
        h2 = client._get_headers("sn=TEST2", "1234567890", "123456")
        assert h1["sign"] != h2["sign"]

    def test_content_type_only_when_requested(self):
        client = _make_client()
        h1 = client._get_headers("", "123", "456", include_content_type=False)
        assert "Content-Type" not in h1

        h2 = client._get_headers("", "123", "456", include_content_type=True)
        assert "Content-Type" in h2
        assert h2["Content-Type"] == "application/json;charset=UTF-8"

    def test_signature_correct_value(self):
        """Verify signature matches manual HMAC-SHA256 computation."""
        client = _make_client()
        params_str = "sn=TEST123"
        timestamp = "1700000000000"
        nonce = "123456"

        headers = client._get_headers(params_str, timestamp, nonce)

        # Manually compute expected signature
        sign_str = f"{params_str}&accessKey=test_access_key&nonce={nonce}&timestamp={timestamp}"
        expected = hmac.new(
            b"test_secret_key",
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert headers["sign"] == expected

    def test_empty_params_signature(self):
        """When no params, signature only from auth params."""
        client = _make_client()
        headers = client._get_headers("", "1700000000000", "123456")

        sign_str = "accessKey=test_access_key&nonce=123456&timestamp=1700000000000"
        expected = hmac.new(
            b"test_secret_key",
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert headers["sign"] == expected


class TestResponseHandling:
    """Test _handle_response error handling."""

    async def test_401_raises_auth_error(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 401
        response.text = AsyncMock(return_value="Unauthorized")

        with pytest.raises(EcoFlowAuthError, match="Authentication failed"):
            await client._handle_response(response)

    async def test_500_raises_api_error(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 500
        response.text = AsyncMock(return_value="Internal Server Error")

        with pytest.raises(EcoFlowApiError, match="status 500"):
            await client._handle_response(response)

    async def test_success_returns_data(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value='{"code":"0","data":{"soc":50}}')
        response.json = AsyncMock(return_value={"code": "0", "data": {"soc": 50}})

        result = await client._handle_response(response)
        assert result == {"soc": 50}

    async def test_success_code_200_int(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value="{}")
        response.json = AsyncMock(return_value={"code": 200, "data": {"key": "val"}})

        result = await client._handle_response(response)
        assert result == {"key": "val"}

    async def test_api_error_code(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value="{}")
        response.json = AsyncMock(return_value={"code": "500", "message": "Something went wrong"})

        with pytest.raises(EcoFlowApiError, match="Something went wrong"):
            await client._handle_response(response)

    async def test_api_error_1006_device_not_allowed(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value="{}")
        response.json = AsyncMock(return_value={"code": 1006, "message": "device not allowed"})

        with pytest.raises(EcoFlowApiError, match="device is not properly bound"):
            await client._handle_response(response)

    async def test_json_parse_error(self):
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value="not json")
        response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        with pytest.raises(EcoFlowApiError, match="Failed to parse"):
            await client._handle_response(response)

    async def test_no_data_key_returns_result(self):
        """When response has no 'data' key, return the full result."""
        client = _make_client()
        response = AsyncMock()
        response.status = 200
        response.text = AsyncMock(return_value="{}")
        response.json = AsyncMock(return_value={"code": "0", "result": "ok"})

        result = await client._handle_response(response)
        assert result == {"code": "0", "result": "ok"}


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_api_error_is_exception(self):
        assert issubclass(EcoFlowApiError, Exception)

    def test_auth_error_is_api_error(self):
        assert issubclass(EcoFlowAuthError, EcoFlowApiError)

    def test_connection_error_is_api_error(self):
        assert issubclass(EcoFlowConnectionError, EcoFlowApiError)
