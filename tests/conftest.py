"""Shared test fixtures for EcoFlow API integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ecoflow_api.commands.base import CommandFormat


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator for entity tests."""
    coordinator = MagicMock()
    coordinator.device_sn = "TEST1234567890"
    coordinator.device_type = "delta_pro_3"
    coordinator.last_update_success = True
    coordinator.data = {}
    coordinator.update_interval_seconds = 15
    coordinator.async_send_command = AsyncMock(return_value=True)
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_set_update_interval = AsyncMock()
    # CoordinatorEntity expects this
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.options = {}
    return entry


@pytest.fixture
def pro_v2_format():
    """Return PRO_V2 command format."""
    return CommandFormat.PRO_V2


@pytest.fixture
def pro_v1_format():
    """Return PRO_V1 command format."""
    return CommandFormat.PRO_V1


@pytest.fixture
def delta_v2_format():
    """Return DELTA_V2 command format."""
    return CommandFormat.DELTA_V2


@pytest.fixture
def smart_plug_format():
    """Return SMART_PLUG command format."""
    return CommandFormat.SMART_PLUG
