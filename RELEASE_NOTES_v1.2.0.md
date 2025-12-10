# 🎉 Release v1.2.0 - Complete Delta Pro 3 Support

## Overview

This release brings **complete Delta Pro 3 support** based on real API data from an actual device! All sensors, controls, and features have been tested and verified with a live Delta Pro 3 unit.

---

## 🌟 What's New

### 📊 **40+ Real Sensors**

All sensor definitions are now based on actual API responses from a real Delta Pro 3 device:

#### 🔋 Battery Sensors
- **BMS Battery Data**
  - Battery Level (BMS) - `bmsBattSoc`
  - State of Health (BMS) - `bmsBattSoh` 
  - Charge/Discharge Remaining Time
  - Design Capacity (80Ah)
  
- **CMS Battery Data**
  - Battery Level (CMS) - `cmsBattSoc`
  - State of Health (CMS) - `cmsBattSoh`
  - Full Energy Capacity (8192Wh)
  - Max/Min Charge Levels

#### ⚡ Power Sensors
- **Input/Output**
  - Total Input Power - `powInSumW`
  - Total Output Power - `powOutSumW`
  
- **AC Power**
  - AC Input Power - `powGetAcIn`
  - AC Output Power - `powGetAc`
  - AC HV/LV Output Power
  - AC Output Frequency
  
- **Solar Power**
  - Solar Input (High Voltage) - `powGetPvH`
  - Solar Input (Low Voltage) - `powGetPvL`
  
- **DC Outputs**
  - 12V DC Output - `powGet12v`
  - 24V DC Output - `powGet24v`
  - USB-C1/C2 Output - `powGetTypec1/2`
  - QC USB1/2 Output - `powGetQcusb1/2`

#### 🌡️ Temperature Sensors
- Max/Min Cell Temperature
- Max/Min MOSFET Temperature

#### ⚙️ Settings Sensors
- AC/DC/Screen Standby Times
- LCD Brightness
- Various operational states

### 🔌 **13 Binary Sensors**

Real-time status indicators:
- AC Charging Active
- Solar Charging (High/Low)
- Battery Pack Charging (4P81/4P82/5P8)
- X-Boost Status
- Beep Status
- Energy Saving Mode
- GFCI Status
- And more...

### 🎛️ **10 Control Entities**

#### Switches (3)
- X-Boost On/Off
- Beep On/Off
- AC Energy Saving

#### Numbers (7)
- AC Charging Power (200-3000W)
- Max Charge Level (50-100%)
- Min Discharge Level (0-30%)
- AC Standby Time (0-1440 min)
- DC Standby Time (0-1440 min)
- Screen Off Time (0-3600 sec)
- LCD Brightness (0-100%)

---

## 📚 **New Documentation**

### DELTA_PRO_3_API_MAPPING.md

Complete API reference including:
- 📋 All API keys with descriptions and examples
- 📊 Data structure breakdown
- 🔧 Available commands
- ⚠️ Known limitations
- 💡 Workarounds and alternatives

### MQTT vs REST API Analysis

Detailed comparison explaining:
- ✅ Why REST API is the right choice
- 📊 Performance comparison
- 🔒 Stability and reliability
- 📖 Official support status
- ⚠️ Cycles availability (MQTT only)

### Template Sensors Examples

Ready-to-use Home Assistant templates:
```yaml
# Estimated Cycles (based on SOH)
# Battery Health Status
# Charging Status (multi-source)
# Net Power Flow
# Runtime Estimates
# Alerts (low battery, high temp)
```

---

## 🧪 **Testing**

This release was tested with:
- **Device**: DELTA Pro 3
- **Serial**: MR51ZES5PG860274
- **Status**: Online, SOH 100%
- **Capacity**: 8192Wh
- **Location**: Europe/Kiev timezone

All sensors verified against real API responses saved in `api_response_MR51ZES5PG860274.json`.

---

## ⚠️ **Important Notes**

### Cycles Not Available in REST API

**Why?**
- Cycle count is only available via **MQTT/WebSocket** protocol
- REST API (`/iot-open/sign/device/quota/all`) does not include this data
- This is a limitation of EcoFlow's Developer API

**Solution:**
We provide a template sensor to **estimate cycles** based on State of Health (SOH):

```yaml
Estimated Cycles ≈ (100 - SOH) × 10
```

For a battery with SOH = 100% (new), estimated cycles ≈ 0  
For a battery with SOH = 90%, estimated cycles ≈ 100

See `examples/template_sensors.yaml` for the complete implementation.

### Why REST API Instead of MQTT?

| Feature | REST API ✅ | MQTT |
|---------|------------|------|
| Official Support | ✅ Yes | ❌ No |
| Stability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ |
| Documentation | ✅ Full | ❌ None |
| Cycles Data | ❌ No | ✅ Yes |
| Update Speed | 15-60s | 1-5s |
| **Recommended** | **✅ Yes** | ⚠️ Optional |

For production use, **REST API is more reliable** and officially supported by EcoFlow.

---

## 🚀 **Installation**

### Via HACS (Recommended)

1. Open HACS
2. Go to Integrations
3. Search for "EcoFlow API"
4. Click Install
5. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy `custom_components/ecoflow_api` to your HA config directory
3. Restart Home Assistant

---

## 📖 **Configuration**

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **EcoFlow API**
4. Enter your:
   - Access Key (from EcoFlow Developer Portal)
   - Secret Key (from EcoFlow Developer Portal)
5. Select your device
6. Configure update interval (default: 15 seconds)

---

## 📝 **Example Usage**

### Basic Dashboard Card

```yaml
type: entities
title: Delta Pro 3
entities:
  - entity: sensor.delta_pro_3_battery_level_bms
  - entity: sensor.delta_pro_3_state_of_health_bms
  - entity: sensor.delta_pro_3_total_input_power
  - entity: sensor.delta_pro_3_total_output_power
  - entity: sensor.delta_pro_3_max_cell_temperature
  - entity: switch.delta_pro_3_x_boost
  - entity: number.delta_pro_3_ac_charging_power
```

### With Template Sensors

```yaml
type: entities
title: Delta Pro 3 Advanced
entities:
  - entity: sensor.delta_pro_3_battery_level_bms
  - entity: sensor.delta_pro_3_estimated_cycles
    name: Estimated Cycles
  - entity: sensor.delta_pro_3_battery_health_status
    name: Battery Health
  - entity: sensor.delta_pro_3_charging_status
    name: Charging Status
  - entity: sensor.delta_pro_3_runtime_estimate
    name: Runtime Left
```

---

## 🔧 **Troubleshooting**

### Sensors Not Updating?

1. Check your API credentials
2. Verify device is online in EcoFlow app
3. Check Home Assistant logs for errors
4. Try increasing update interval

### Controls Not Working?

1. Ensure device is online
2. Check API permissions in EcoFlow Developer Portal
3. Verify command codes in logs
4. Try the device control from EcoFlow app first

### Missing Cycles Sensor?

This is expected! Cycles are not available via REST API. Use the template sensor from `examples/template_sensors.yaml` to estimate cycles based on SOH.

---

## 🙏 **Acknowledgments**

- Thanks to EcoFlow for providing the Developer API
- Thanks to [@tolwi](https://github.com/tolwi/hassio-ecoflow-cloud) for inspiration
- Thanks to the Home Assistant community

---

## 📞 **Support**

- 🐛 **Issues**: [GitHub Issues](https://github.com/TarasKhust/hassio-ecoflow-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/TarasKhust/hassio-ecoflow-api/discussions)
- 📖 **Documentation**: [README.md](README.md)

---

## 🔮 **What's Next?**

Planned for future releases:
- 🔄 Support for more EcoFlow devices (Delta 2, River series)
- 📊 Energy dashboard integration
- 🔔 Advanced automations examples
- 🌐 More translations
- 📱 Optional MQTT support for real-time data

---

**Enjoy your Delta Pro 3 integration!** ⚡🔋

If you find this integration useful, please ⭐ star the repository!



