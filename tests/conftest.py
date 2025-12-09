"""Common test fixtures."""
import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


@pytest.fixture
def hass(event_loop):
    """Create a test Home Assistant instance."""
    hass = HomeAssistant()
    hass.config.config_dir = "/tmp/test_home_assistant"
    
    yield hass
    
    event_loop.run_until_complete(hass.async_stop())


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Enable custom integrations."""
    with patch(
        "homeassistant.loader.async_get_custom_components",
        return_value={},
    ):
        yield

