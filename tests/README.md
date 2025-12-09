# EcoFlow API Integration Tests

This directory contains tests for the EcoFlow API Home Assistant integration.

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Shared pytest fixtures
├── test_api.py              # API client tests
├── test_config_flow.py      # Config flow tests
└── test_simple.py           # Simple unit tests
```

## Running Tests

### Option 1: Structure Check (No Dependencies)

Run the structure validation script to verify all files are in place:

```bash
python check_structure.py
```

This checks:
- ✅ All required files exist
- ✅ Device module structure is correct
- ✅ Manifest.json is valid
- ✅ Translations are present
- ✅ Test files are configured

### Option 2: Unit Tests (Requires pytest)

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Run all tests:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_api.py -v
```

Run with coverage:

```bash
pytest tests/ --cov=custom_components.ecoflow_api --cov-report=html
```

### Option 3: Home Assistant Test Environment

For integration testing with Home Assistant:

```bash
# Install Home Assistant
pip install homeassistant

# Run tests
pytest tests/ -v --tb=short
```

## Test Coverage

### ✅ API Client (`test_api.py`)
- Signature generation
- Nonce generation (6 digits)
- Parameter flattening (nested objects, arrays)
- Parameter sorting and concatenation
- Device list retrieval
- Device quota retrieval
- Device quota setting
- Error handling (API errors, auth errors)
- Command building for Delta Pro 3

### ✅ Config Flow (`test_config_flow.py`)
- User flow with auto discovery
- User flow with manual entry
- Options flow (update interval configuration)

### ✅ Module Structure (`test_simple.py`)
- Constants validation
- Device module imports
- Delta Pro 3 constants
- Command base structure

## Manual Testing

For manual testing with real API credentials, create test files in the root directory (they are in `.gitignore`):

```python
# test_my_device.py
import asyncio
import aiohttp
from custom_components.ecoflow_api.api import EcoFlowApiClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = EcoFlowApiClient(
            access_key="YOUR_ACCESS_KEY",
            secret_key="YOUR_SECRET_KEY",
            session=session,
        )
        
        # Test device list
        devices = await client.get_device_list()
        print(f"Devices: {devices}")
        
        # Test quota
        if devices:
            sn = devices[0]["sn"]
            quota = await client.get_device_quota(sn)
            print(f"Quota: {quota}")

asyncio.run(main())
```

⚠️ **Important**: Test files with credentials should match patterns in `.gitignore`:
- `test_*.py` (in root)
- `*_test.py` (in root)
- `get_device_data.py`
- `test_device_controls.py`

## CI/CD Integration

To add automated testing to GitHub Actions, create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run structure check
        run: python check_structure.py
      - name: Run tests
        run: pytest tests/ -v
```

## Writing New Tests

### Adding Device-Specific Tests

When adding support for new devices (e.g., River 2, Delta 2 Max):

1. Create device constants test:
```python
# tests/test_devices.py
def test_river_2_constants():
    from custom_components.ecoflow_api.devices.river_2 import (
        DEVICE_TYPE,
        COMMAND_BASE,
    )
    assert DEVICE_TYPE == "River 2"
    assert "cmdId" in COMMAND_BASE
```

2. Test device-specific commands:
```python
async def test_river_2_commands(mock_api_client):
    # Test River 2 specific commands
    pass
```

### Testing New Sensors/Controls

When adding new sensors, switches, numbers, or selects:

```python
def test_new_sensor_definition():
    from custom_components.ecoflow_api.sensor import SENSORS
    
    # Check sensor exists
    assert "new_sensor_key" in SENSORS
    
    # Verify sensor properties
    sensor = SENSORS["new_sensor_key"]
    assert sensor.name == "Expected Name"
    assert sensor.device_class == "expected_class"
```

## Troubleshooting

### ImportError: No module named 'homeassistant'

Install Home Assistant:
```bash
pip install homeassistant
```

Or run structure check instead (no HA required):
```bash
python check_structure.py
```

### Tests Pass Locally But Fail in CI

Check Python version compatibility:
- Integration requires Python 3.11+
- Home Assistant 2024.1.0+

### API Signature Tests Failing

Verify signature generation matches EcoFlow API docs:
1. 6-digit nonce
2. Parameters sorted by ASCII
3. HMAC-SHA256 with secret key
4. Convert to hex string

