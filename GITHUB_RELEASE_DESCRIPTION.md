# 🎉 Complete Delta Pro 3 Support

This release brings **complete Delta Pro 3 support** based on real API data from an actual device! All sensors, controls, and features have been tested and verified with a live Delta Pro 3 unit.

---

## 🌟 What's New

### 📊 **40+ Real Sensors**
All sensor definitions are now based on actual API responses:

- 🔋 **Battery**: BMS & CMS data (SOC, SOH, remaining time, capacity)
- ⚡ **Power**: Input/Output, AC, Solar (HV/LV), DC (12V/24V), USB-C, QC USB
- 🌡️ **Temperature**: Min/Max cell and MOSFET temperatures
- ⚙️ **Settings**: Standby times, LCD brightness, frequency

### 🔌 **13 Binary Sensors**
- AC/Solar/Battery charging status
- X-Boost, Beep, Energy Saving modes
- GFCI status and more

### 🎛️ **10 Control Entities**
- **3 Switches**: X-Boost, Beep, AC Energy Saving
- **7 Numbers**: AC charging power (200-3000W), charge levels, standby times, LCD brightness

### 📚 **Comprehensive Documentation**
- 📖 **[DELTA_PRO_3_API_MAPPING.md](DELTA_PRO_3_API_MAPPING.md)** - Complete API reference with real data examples
- 🔍 **MQTT vs REST API** - Detailed comparison and recommendations
- 📝 **Cycles explanation** - Why cycles are not available in REST API and alternatives
- 🧪 **[Template sensors](examples/template_sensors.yaml)** - Ready-to-use Home Assistant templates

---

## 🧪 Tested with Real Device

- **Device**: DELTA Pro 3
- **Serial**: MR51ZES5PG860274
- **Status**: Online, SOH 100%
- **Capacity**: 8192Wh
- **Location**: Europe/Kiev

All sensors verified against real API responses!

---

## ⚠️ Important Notes

### Cycles Not Available in REST API

**Why?**
- Cycle count is only available via **MQTT/WebSocket** protocol
- REST API does not include this data
- This is a limitation of EcoFlow's Developer API

**Solution:**
We provide a template sensor to **estimate cycles** based on State of Health (SOH):

```yaml
Estimated Cycles ≈ (100 - SOH) × 10
```

See [examples/template_sensors.yaml](examples/template_sensors.yaml) for the complete implementation.

### Why REST API?

| Feature | REST API ✅ | MQTT |
|---------|------------|------|
| Official Support | ✅ Yes | ❌ No |
| Stability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ |
| Documentation | ✅ Full | ❌ None |
| Cycles Data | ❌ No | ✅ Yes |
| **Recommended** | **✅ Yes** | ⚠️ Optional |

For production use, **REST API is more reliable** and officially supported by EcoFlow.

---

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS → Integrations
2. Search for "EcoFlow API"
3. Click Install
4. Restart Home Assistant

### Manual Installation

1. Download `ecoflow-api-v1.2.0.zip`
2. Extract to `config/custom_components/`
3. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **EcoFlow API**
4. Enter your Access Key and Secret Key from [EcoFlow Developer Portal](https://developer-eu.ecoflow.com/)
5. Select your device
6. Configure update interval (default: 15 seconds)

---

## 📝 Example Usage

### Basic Dashboard

```yaml
type: entities
title: Delta Pro 3
entities:
  - entity: sensor.delta_pro_3_battery_level_bms
  - entity: sensor.delta_pro_3_state_of_health_bms
  - entity: sensor.delta_pro_3_total_input_power
  - entity: sensor.delta_pro_3_total_output_power
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
  - entity: sensor.delta_pro_3_battery_health_status
  - entity: sensor.delta_pro_3_charging_status
  - entity: sensor.delta_pro_3_runtime_estimate
```

See [examples/template_sensors.yaml](examples/template_sensors.yaml) for complete template definitions.

---

## 🔧 What's Changed

### Added
- 40+ sensors based on real Delta Pro 3 device data
- 13 binary sensors for status monitoring
- 10 control entities (3 switches, 7 numbers)
- Complete API documentation with examples
- Template sensors for estimated cycles and more
- MQTT vs REST API comparison
- Comprehensive testing with real device

### Changed
- All sensor definitions updated with actual API keys
- Improved sensor naming (BMS vs CMS)
- Enhanced documentation

### Technical Details
- Tested with real device (SN: MR51ZES5PG860274)
- API endpoint verified: `/iot-open/sign/device/quota/all`
- Authentication working with EcoFlow Developer API
- Timezone support (Europe/Kiev tested)

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/TarasKhust/hassio-ecoflow-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/TarasKhust/hassio-ecoflow-api/discussions)
- 📖 **Documentation**: [README.md](README.md)

---

## 🙏 Acknowledgments

- Thanks to EcoFlow for providing the Developer API
- Thanks to [@tolwi](https://github.com/tolwi/hassio-ecoflow-cloud) for inspiration
- Thanks to the Home Assistant community

---

**Full Changelog**: https://github.com/TarasKhust/hassio-ecoflow-api/blob/main/CHANGELOG.md

**Enjoy your Delta Pro 3 integration!** ⚡🔋

If you find this integration useful, please ⭐ star the repository!



