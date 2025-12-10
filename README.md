# EcoFlow API Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/TarasKhust/hassio-ecoflow-api.svg?style=flat-square)](https://github.com/TarasKhust/hassio-ecoflow-api/releases)
[![License](https://img.shields.io/github/license/TarasKhust/hassio-ecoflow-api.svg?style=flat-square)](LICENSE)

Home Assistant integration for EcoFlow devices using the **official EcoFlow Developer API**.

## 🌟 Features

- ✅ **Official API** - Uses EcoFlow Developer REST API (stable & documented)
- ✅ **Complete Delta Pro 3 support** - 40+ sensors, 13 binary sensors, 10 controls
- ✅ **Real device tested** - All features verified with actual Delta Pro 3
- ✅ **Battery monitoring** - BMS & CMS data, SOC, SOH, temperature, capacity
- ✅ **Power monitoring** - Input/output, AC, Solar (HV/LV), DC (12V/24V), USB-C, QC USB
- ✅ **Full control** - AC charging power, charge levels, standby times, X-Boost, outputs
- ✅ **Extra Battery support** - Automatic detection and monitoring
- ✅ **Template sensors** - Estimated cycles, health status, runtime calculations
- ✅ **Device discovery** - Automatic device detection from API
- ✅ **Ukrainian localization** - Повна підтримка української мови
- 📚 **Comprehensive docs** - Complete API mapping and examples

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL and select "Integration" category
5. Search for "EcoFlow API" and install
6. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Extract and copy `custom_components/ecoflow_api` to your `config/custom_components/` directory
3. Restart Home Assistant

## ⚙️ Configuration

### Prerequisites

1. **EcoFlow Developer Account**: Register at [EcoFlow Developer Portal](https://developer-eu.ecoflow.com/)
2. **API Credentials**: Create an application and get your Access Key and Secret Key
3. **Device Serial Number**: Find it on your device or in the EcoFlow app

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "EcoFlow API"
4. Choose setup method:
   - **Automatic Discovery**: Enter credentials, integration finds your devices
   - **Manual Entry**: Manually enter device serial number and type
5. Enter your credentials:
   - **Access Key**: Your EcoFlow Developer API access key
   - **Secret Key**: Your EcoFlow Developer API secret key
   - **Device Serial Number**: Your device's serial number (manual mode)
   - **Device Type**: Select your device model (manual mode)

### Options

After setup, you can configure additional options:

1. Go to **Settings** → **Devices & Services**
2. Find "EcoFlow API" integration
3. Click **Configure**
4. Adjust settings:
   - **Update Interval**: How often to poll the device (5-60 seconds, default: 15s)
     - 5s: Fast updates (more API calls)
     - 15s: Recommended balance
     - 60s: Slower updates (fewer API calls)

## 📊 Entities

### Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| Battery Level | Current battery percentage | % |
| State of Health | Battery health status | % |
| Cycles | Charge cycle count | - |
| Full Capacity | Battery full capacity | Wh |
| Remaining Capacity | Remaining battery capacity | Wh |
| Total In Power | Total input power | W |
| Total Out Power | Total output power | W |
| AC In Power | AC input power | W |
| AC Out Power | AC output power | W |
| Solar In Power | Solar panel input | W |
| DC Out Power | DC output power | W |
| Charge Remaining Time | Time to full charge | min |
| Discharge Remaining Time | Time to empty | min |
| Battery Temperature | Battery temperature | °C |
| Battery Voltage | Battery voltage | V |
| Battery Current | Battery current | A |
| **Extra Battery 1/2** | All above sensors for extra batteries | - |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| AC Input Connected | AC input connection status |
| Solar Input Connected | Solar panel connection status |
| Charging | Device is charging |
| Discharging | Device is discharging |
| AC Output Enabled | AC output is enabled |
| DC Output Enabled | DC output is enabled |
| Battery Low | Battery level below 20% |
| Battery Full | Battery fully charged |
| Over Temperature | Battery temperature above 45°C |
| **Extra Battery Connected** | Extra battery connection status | - |
| **Extra Battery Low/Full** | Extra battery level status | - |

### Switches

| Entity | Description |
|--------|-------------|
| AC Output | Toggle AC output on/off |
| DC Output | Toggle DC output on/off |
| 12V DC Output | Toggle 12V DC output on/off |
| Beeper | Toggle beeper on/off |
| X-Boost | Toggle X-Boost on/off |

### Numbers (Sliders)

| Entity | Description | Range |
|--------|-------------|-------|
| AC Charging Power | Set charging power | 200-3000 W |
| Max Charge Level | Maximum charge level | 50-100% |
| Min Discharge Level | Minimum discharge level | 0-30% |

## 🔧 Automations

### Example: Smart Charging Based on Power Outage Schedule

```yaml
alias: EcoFlow - Smart Charging
description: Automatically adjust charging power based on outage schedule
trigger:
  - platform: time_pattern
    minutes: "/15"
condition:
  - condition: numeric_state
    entity_id: sensor.ecoflow_delta_pro_3_ac_in_power
    above: 0
action:
  - service: number.set_value
    target:
      entity_id: number.ecoflow_delta_pro_3_ac_charging_power
    data:
      value: >
        {% if states('sensor.yasno_status') == 'emergency_shutdowns' %}
          2900
        {% else %}
          1000
        {% endif %}
mode: single
```

### Example: Battery Level Notifications

```yaml
alias: EcoFlow - Low Battery Alert
trigger:
  - platform: numeric_state
    entity_id: sensor.ecoflow_delta_pro_3_battery_level
    below: 20
action:
  - service: notify.notify
    data:
      title: "⚠️ Low Battery"
      message: "EcoFlow battery is at {{ states('sensor.ecoflow_delta_pro_3_battery_level') }}%"
mode: single
```

## 🌍 Supported Devices

| Device | Status | Notes |
|--------|--------|-------|
| Delta Pro 3 | ✅ Full Support | All features |
| Delta Pro | 🔄 Planned | Coming soon |
| Delta 2 | 🔄 Planned | Coming soon |
| Delta 2 Max | 🔄 Planned | Coming soon |
| River 2 | 🔄 Planned | Coming soon |
| River 2 Max | 🔄 Planned | Coming soon |

## 🧪 Testing

The integration includes comprehensive tests to ensure reliability:

```bash
# Quick structure check (no dependencies required)
python check_structure.py

# Full test suite (requires pytest)
pip install -r requirements-test.txt
pytest tests/ -v
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 📚 Documentation

- [EcoFlow Developer API](https://developer-eu.ecoflow.com/us/document/introduction)
- [Delta Pro 3 API Reference](https://developer-eu.ecoflow.com/us/document/deltaPro3)
- [Testing Guide](tests/README.md)

## 🐛 Troubleshooting

### Common Issues

**1. "Failed to connect to EcoFlow API"**
- Check your internet connection
- Verify your Access Key and Secret Key
- Ensure your developer account is active

**2. "Device not found"**
- Verify the serial number is correct
- Check that the device is online in the EcoFlow app
- Ensure the device is linked to your developer account

**3. Values not updating**
- The integration polls every 15 seconds by default (configurable: 5-60 seconds)
- You can adjust the update interval in integration options
- Check Home Assistant logs for errors
- Try reloading the integration

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ecoflow_api: debug
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [EcoFlow](https://www.ecoflow.com/) for providing the Developer API
- [Home Assistant](https://www.home-assistant.io/) community
- [hassio-ecoflow-cloud](https://github.com/tolwi/hassio-ecoflow-cloud) for inspiration

## ☕ Support

If you find this integration useful, consider:

- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting features
- 🇺🇦 Supporting Ukraine

---

Made with ❤️ in Ukraine 🇺🇦


