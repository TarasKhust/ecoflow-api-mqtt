# Release v1.3.0-beta1 - Hybrid REST API + MQTT Support (BETA)

## ⚠️ Beta Release

This is a **beta release** for testing the new hybrid REST API + MQTT functionality. Please test thoroughly and report any issues!

## 🎉 What's New

### Hybrid REST API + MQTT Support
The integration now supports **both REST API and MQTT** for the best of both worlds!

**Why Hybrid?**
- 🚀 **REST API**: Official, stable, reliable device control
- ⚡ **MQTT**: Real-time updates, more data points, lower latency
- 🔄 **Together**: Instant updates + reliable control

### Key Features

#### 1. Real-Time Updates via MQTT
- ⚡ Instant sensor updates (no polling delay)
- 📊 Additional data: **Battery Cycles** sensor now available!
- 🔋 Lower battery drain (less frequent API calls)
- 📡 WebSocket-based MQTT connection to `mqtt.ecoflow.com`

#### 2. Reliable Control via REST API
- 🎛️ All device controls use REST API (proven, stable)
- ✅ AC/DC output, charging power, X-Boost, etc.
- 🔐 Official EcoFlow Developer API

#### 3. Intelligent Fallback
- 🔄 Automatically falls back to REST-only if MQTT unavailable
- 📉 Reduces REST polling frequency when MQTT active (4x less)
- 🛡️ Graceful degradation - always works

#### 4. Easy Configuration
- ⚙️ Enable/disable MQTT in Settings → Configure
- 📧 Uses your EcoFlow account credentials (email/password)
- 🔌 Works perfectly fine without MQTT (REST-only mode)

## 📊 New Sensors (MQTT-only)

- **Battery Cycles** (`sensor.ecoflow_delta_pro_3_battery_cycles`) - Finally available! 🎉

## 🚀 How to Enable MQTT

1. **Update the integration** (HACS or manual)
2. **Restart Home Assistant**
3. Go to **Settings → Devices & Services → EcoFlow API**
4. Click **⚙️ Configure**
5. Enable **MQTT Enabled**
6. Enter your **EcoFlow account email** (MQTT Username)
7. Enter your **EcoFlow account password** (MQTT Password)
8. Click **Submit**
9. Check logs for "MQTT connected successfully"

## 📦 Installation

### Via HACS (Recommended)
1. Go to HACS → Integrations
2. Find "EcoFlow API"
3. Click "Update" or "Redownload"
4. Select version **v1.3.0-beta1**
5. Restart Home Assistant

### Manual Installation
1. Download `ecoflow-api-v1.3.0-beta1.zip` from this release
2. Extract to `custom_components/ecoflow_api/`
3. Restart Home Assistant

## 🧪 Testing Checklist

Please test and report:
- [ ] MQTT connection establishes successfully
- [ ] Real-time sensor updates work
- [ ] Battery Cycles sensor appears and updates
- [ ] Device controls still work (AC/DC output, etc.)
- [ ] Fallback to REST-only if MQTT disabled
- [ ] Integration works without MQTT configured
- [ ] No errors in Home Assistant logs

## 🐛 Known Limitations

- MQTT requires EcoFlow account credentials (email/password)
- MQTT broker: `mqtt.ecoflow.com:8883` (cannot be changed)
- Some sensors may only be available via MQTT or REST (not both)

## 📝 Technical Details

**New Files:**
- `mqtt_client.py` - MQTT client implementation
- `hybrid_coordinator.py` - Hybrid REST+MQTT coordinator

**Modified Files:**
- `__init__.py` - Hybrid coordinator initialization
- `config_flow.py` - MQTT configuration in OptionsFlow
- `const.py` - MQTT-only sensors, MQTT config constants
- `manifest.json` - Added `paho-mqtt>=1.6.1` dependency

**Connection Modes:**
- `hybrid` - MQTT connected, REST as backup
- `mqtt_standby` - MQTT connected but not primary
- `rest_only` - MQTT disabled or unavailable

## 🔗 Links

- [Full Changelog](CHANGELOG.md)
- [Documentation](README.md)
- [Issue Tracker](https://github.com/TarasKhust/hassio-ecoflow-api/issues)
- [Linear Task MON-12](https://linear.app/moneymanagerapp/issue/MON-12)

## 💬 Feedback

**This is a BETA release!** Please test and provide feedback:
- Report issues: https://github.com/TarasKhust/hassio-ecoflow-api/issues
- Discuss: https://github.com/TarasKhust/hassio-ecoflow-api/discussions

Your feedback helps make this integration better! 🙏

---

**Full Changelog**: https://github.com/TarasKhust/hassio-ecoflow-api/compare/v1.2.1...v1.3.0-beta1

