# EcoFlow API Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/TarasKhust/ecoflow-api-mqtt.svg?style=flat-square)](https://github.com/TarasKhust/ecoflow-api-mqtt/releases)
[![License](https://img.shields.io/github/license/TarasKhust/ecoflow-api-mqtt.svg?style=flat-square)](LICENSE)

> ⚠️ **License Notice**: This software is free for personal and non-commercial use only. Commercial use is prohibited without explicit permission. See [LICENSE](LICENSE) for details.

Home Assistant integration for EcoFlow devices using the **official EcoFlow Developer API**.

## 🌟 Features

- ✅ **Hybrid Mode** - Combines REST API + MQTT for best performance
  - Real-time updates via MQTT (instant sensor updates)
  - Device control via REST API (reliable commands)
  - Automatic fallback to REST polling if MQTT unavailable
- ✅ **Official API** - Uses EcoFlow Developer REST API (stable & documented)
- ✅ **Multi-device support** - Delta Pro 3, Delta Pro, Delta 2, Stream Ultra X
- ✅ **Region support** - EU and US API endpoints
- ✅ **Complete Delta Pro 3 support** - 100+ sensors, 13 binary sensors, 12 switches, 16 number controls, Power Off button
- ✅ **Complete Delta 2 support** - 150+ sensors with value mapping, Extra Battery support
- ✅ **Real device tested** - All features verified with actual Delta Pro 3
- ✅ **Battery monitoring** - BMS & CMS data, SOC, SOH, temperature, capacity
- ✅ **Power monitoring** - Input/output, AC, Solar (HV/LV), DC (12V/24V), USB-C, QC USB
- ✅ **Full control** - AC charging power, charge levels, standby times, X-Boost, outputs
- ✅ **Extra Battery support** - Automatic detection and monitoring
- ✅ **Template sensors** - Estimated cycles, health status, runtime calculations
- ✅ **Device discovery** - Automatic device detection from API
- ✅ **Ukrainian localization** - Повна підтримка української мови

## 📦 Installation

### HACS (Recommended)

**Quick Install:**
[![Open your Home Assistant instance and show the repository.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TarasKhust&repository=ecoflow-api-mqtt&category=integration)

**Manual Setup:**

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL: `https://github.com/TarasKhust/ecoflow-api-mqtt` and select "Integration" category
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
   - **Region**: Select EU (Europe) or US (United States)
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
   - **Update Interval**: How often to poll the device via REST API (5-60 seconds, default: 15s)
     - 5s: Fast updates (more API calls)
     - 15s: Recommended balance
     - 60s: Slower updates (fewer API calls)
     - **Note**: In hybrid mode, REST polling is automatically reduced since MQTT provides real-time updates
   - **MQTT Enabled**: Enable hybrid mode (REST API + MQTT)
     - When enabled, integration automatically fetches MQTT credentials from API
     - Provides real-time sensor updates via MQTT
     - Device control still uses REST API for reliability
     - Automatically falls back to REST-only if MQTT connection fails
   - **MQTT Username/Password**: Optional manual MQTT credentials (usually auto-fetched from API)

## 📊 Entities

### Sensors

| Entity                   | Description                           | Unit |
| ------------------------ | ------------------------------------- | ---- |
| Battery Level            | Current battery percentage            | %    |
| State of Health          | Battery health status                 | %    |
| Cycles                   | Charge cycle count                    | -    |
| Full Capacity            | Battery full capacity                 | Wh   |
| Remaining Capacity       | Remaining battery capacity            | Wh   |
| Total In Power           | Total input power                     | W    |
| Total Out Power          | Total output power                    | W    |
| AC In Power              | AC input power                        | W    |
| AC Out Power             | AC output power                       | W    |
| Solar In Power           | Solar panel input                     | W    |
| DC Out Power             | DC output power                       | W    |
| Charge Remaining Time    | Time to full charge                   | min  |
| Discharge Remaining Time | Time to empty                         | min  |
| Battery Temperature      | Battery temperature                   | °C   |
| Battery Voltage          | Battery voltage                       | V    |
| Battery Current          | Battery current                       | A    |
| **Extra Battery 1/2**    | All above sensors for extra batteries | -    |

### Binary Sensors

| Entity                      | Description                     |
| --------------------------- | ------------------------------- | --- |
| AC Input Connected          | AC input connection status      |
| Solar Input Connected       | Solar panel connection status   |
| Charging                    | Device is charging              |
| Discharging                 | Device is discharging           |
| AC Output Enabled           | AC output is enabled            |
| DC Output Enabled           | DC output is enabled            |
| Battery Low                 | Battery level below 20%         |
| Battery Full                | Battery fully charged           |
| Over Temperature            | Battery temperature above 45°C  |
| **Extra Battery Connected** | Extra battery connection status | -   |
| **Extra Battery Low/Full**  | Extra battery level status      | -   |

### Switches

| Entity        | Description                 |
| ------------- | --------------------------- |
| AC Output     | Toggle AC output on/off     |
| DC Output     | Toggle DC output on/off     |
| 12V DC Output | Toggle 12V DC output on/off |
| Beeper        | Toggle beeper on/off        |
| X-Boost       | Toggle X-Boost on/off       |

### Numbers (Sliders)

| Entity              | Description             | Range      |
| ------------------- | ----------------------- | ---------- |
| AC Charging Power   | Set charging power      | 200-3000 W |
| Max Charge Level    | Maximum charge level    | 50-100%    |
| Min Discharge Level | Minimum discharge level | 0-30%      |

## 📐 Template Sensors

### Formatted Remaining Time Sensor

If you want to display remaining time in a formatted way (e.g., "2h 37m" instead of "157 min"), you can create a template sensor:

```yaml
# Add to configuration.yaml or as a separate file in configuration/sensors/
template:
  - sensor:
      - name: "Delta Pro 3 Remaining Time"
        unique_id: delta_pro_3_remaining_time
        state: >
          {% set in_power = states('sensor.ecoflow_delta_pro_3_total_input_power') | float(0) %}
          {% set out_power = states('sensor.ecoflow_delta_pro_3_total_output_power') | float(0) %}
          {% if in_power > 0 and in_power >= out_power %}
            {% set time_val = states('sensor.ecoflow_delta_pro_3_system_charge_remaining_time') | float(0) %}
          {% elif out_power > 0 %}
            {% set time_val = states('sensor.ecoflow_delta_pro_3_system_discharge_remaining_time') | float(0) %}
          {% else %}
            {% set time_val = 0 %}
          {% endif %}
          {% if time_val > 0 %}
            {% set hours = (time_val / 60) | int %}
            {% set mins = (time_val % 60) | int %}
            {{ hours }}h {{ mins }}m
          {% else %}
            -
          {% endif %}
        icon: >
          {% set in_power = states('sensor.ecoflow_delta_pro_3_total_input_power') | float(0) %}
          {% set out_power = states('sensor.ecoflow_delta_pro_3_total_output_power') | float(0) %}
          {% if in_power > 0 and in_power >= out_power %}
            mdi:battery-charging
          {% else %}
            mdi:battery-arrow-down
          {% endif %}
```

**Important:** The remaining time sensors return values in **minutes** (not hours), so you need to divide by 60 to get hours and use modulo to get remaining minutes.

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

| Device          | Status          | Notes                            |
| --------------- | --------------- | -------------------------------- |
| Delta Pro 3     | ✅ Full Support | All features, real device tested |
| Delta Pro       | ✅ Full Support | US API verified                  |
| Delta 2         | ✅ Full Support | 150+ sensors, Extra Battery, real device tested |
| Stream Ultra X  | ✅ Full Support | Home battery system (Issue #16)  |
| Delta 2 Max     | 🔄 Planned      | Coming soon                      |
| River 2         | 🔄 Planned      | Coming soon                      |
| River 2 Max     | 🔄 Planned      | Coming soon                      |

### Stream Ultra X

Stream Ultra X (BK61 series) is a home battery/balcony power system with grid connection support.

| Feature | Details |
| ------- | ------- |
| **Sensors** | Battery level, solar power, grid power, system load, backup reserve |
| **Controls** | AC1/AC2 switches, feed-in control, operating mode (Self-Powered/AI Mode) |
| **Numbers** | Backup reserve level (3-95%), charge/discharge limits |
| **Binary** | Battery charging/discharging, solar generating, grid feed-in/consuming |

**Supported Stream Models:**
- STREAM Ultra X (BK61)
- STREAM Ultra, STREAM Pro, STREAM AC Pro
- STREAM Max, STREAM AC
- STREAM Ultra (US)

### Delta 2 Sensors

Delta 2 has extensive sensor support with human-readable value mapping:

| Category | Sensors | Examples |
| -------- | ------- | -------- |
| **BMS** | 35+ | Battery level, voltage, current, temperature, cycles, SOH, MOS temps, accumulated energy |
| **EMS** | 15+ | Charge/discharge state, fan level, UPS mode, warning state, parallel voltage |
| **PD** | 30+ | Port status, DC/AC/Car output state, cumulative energy (AC/DC/Solar), usage time |
| **INV** | 20+ | AC charging power, DC input, fan state, X-Boost, work mode, charger type |
| **MPPT** | 25+ | Solar input, charge type/state, car charger, DC24V state, beep mode |
| **Extra Battery** | 8 | Connected status, SOC, power for up to 2 extra batteries |

**Value Mapping Examples:**
- Port Status: `null`, `extra_battery`, `smart_generator`, `cc`, `pr`, `sp_bc`
- Charge Type: `adapter`, `mppt_solar`, `ac`, `gas`, `wind`
- Fan Level: `off`, `level_1`, `level_2`, `level_3`
- States: `charging`/`not_charging`, `on`/`off`, `normal`/`silent`

### Region Support

The integration supports both **EU** and **US** API endpoints:

- **Europe**: api-e.ecoflow.com
- **United States**: api.ecoflow.com

Select your region during setup.

## 🔄 Hybrid Mode (REST API + MQTT)

The integration supports a **hybrid mode** that combines the best of both worlds:

### How It Works

- **REST API**: Used for device control (commands, settings) - reliable and documented
- **MQTT**: Used for real-time sensor updates - instant notifications when device state changes
- **Automatic Fallback**: If MQTT connection fails, automatically falls back to REST-only mode

### Benefits

- ⚡ **Real-time updates** - Sensor values update instantly via MQTT (no polling delay)
- 🔧 **Reliable control** - Device commands use REST API (more stable)
- 📉 **Reduced API calls** - REST polling interval automatically increases when MQTT is active
- 🛡️ **Automatic recovery** - Seamlessly switches between modes based on availability

### Enabling Hybrid Mode

1. Go to **Settings** → **Devices & Services**
2. Find "EcoFlow API" integration
3. Click **Configure**
4. Enable **MQTT Enabled** checkbox
5. MQTT credentials are automatically fetched from API (no manual entry needed)
6. Save and restart the integration

The integration will automatically:

- Fetch MQTT credentials (`certificateAccount` and `certificatePassword`) from EcoFlow API
- Connect to EcoFlow MQTT broker
- Start receiving real-time updates
- Reduce REST API polling frequency (since MQTT provides updates)

### Connection Status

You can monitor the connection mode via the `sensor.ecoflow_delta_pro_3_connection_mode` sensor:

- `hybrid` - Both REST API and MQTT active (optimal)
- `mqtt_standby` - MQTT connected but not actively used
- `rest_only` - REST API only (MQTT unavailable or disabled)

## 🐛 Debug Mode

To enable debug logging for troubleshooting, add the following to your `/homeassistant/configuration.yaml`:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.ecoflow_api: debug
```

After adding this configuration:
1. Restart Home Assistant
2. Check logs in **Settings** → **System** → **Logs**
3. Filter by "ecoflow" to see integration-specific logs

Debug logs include:
- API request/response details
- MQTT connection status
- Sensor value updates
- Command execution results

> ⚠️ **Note**: Debug mode generates a lot of log data. Disable it after troubleshooting by removing the configuration or changing `debug` to `info`.

## 📚 Documentation

- [EcoFlow Developer API](https://developer-eu.ecoflow.com/us/document/introduction)
- [Delta Pro 3 API Reference](https://developer-eu.ecoflow.com/us/document/deltaPro3)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is licensed under a **Non-Commercial License** - see the [LICENSE](LICENSE) file for details.

**Important:** This software is free to use for personal and non-commercial purposes only. Commercial use is prohibited without explicit permission from the copyright holder. For commercial licensing inquiries, please contact the maintainer.

## 🙏 Acknowledgments

- [EcoFlow](https://www.ecoflow.com/) for providing the Developer API
- [Home Assistant](https://www.home-assistant.io/) community

## ☕ Support

You can support this project by:

- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting features
- 🇺🇦 Supporting Ukraine

---

Made with ❤️ in Ukraine 🇺🇦
