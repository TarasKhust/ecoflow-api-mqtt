# v1.3.0-beta9 - Energy Dashboard Integration + MQTT Fix

## 🎉 Major Features

### ⚡ Full Energy Dashboard Integration
The integration now automatically creates energy sensors (kWh) from all power sensors (W), making it fully compatible with Home Assistant's Energy Dashboard!

**What's included:**
- **Automatic Energy Sensors** - Power sensors (W) automatically get companion energy sensors (kWh)
  - `Total Input Power` → `Total Input Energy` (enabled)
  - `Total Output Power` → `Total Output Energy` (enabled)
  - `AC Input Power` → `AC Input Energy` (disabled by default)
- **Power Difference Sensor** - Shows net power flow (Input - Output)
  - Positive = charging/receiving power ⚡
  - Negative = discharging/consuming power 🔋
  - Perfect for Energy Dashboard "Now" tab

### 🗄️ Database Optimization
- **Recorder Exclusions** - Technical attributes excluded from history
- Reduces database size and improves Home Assistant performance
- Excludes: `mqtt_connected`, `last_update_time`, `device_info`, etc.

### 🔐 MQTT Authentication (from beta8)
- Fixed "Connection Refused - not authorized (code 5)" error
- Automatically fetches `certificateAccount` and `certificatePassword` from API
- No manual MQTT credentials needed!

---

## 📊 How to Use Energy Dashboard

### 1. Enable Energy Dashboard
Go to **Configuration** → **Energy** in Home Assistant

### 2. Add Grid Consumption (if using AC input)
- Source: `sensor.ecoflow_delta_pro_3_total_input_energy`
- This tracks energy consumed from the grid

### 3. Add Grid Return (if feeding back to grid)
- Source: `sensor.ecoflow_delta_pro_3_total_output_energy`
- This tracks energy returned to the grid

### 4. Add Battery (if using as backup)
- Source: `sensor.ecoflow_delta_pro_3_power_difference`
- This shows real-time charging/discharging

### 5. View Statistics
- **Energy Tab** - Daily/Monthly consumption charts
- **Now Tab** - Real-time power flow visualization
- **Devices Tab** - Individual device consumption

---

## 🆕 New Sensors

| Sensor | Description | Enabled by Default |
|--------|-------------|-------------------|
| `Total Input Energy` | kWh consumed from all inputs | ✅ Yes |
| `Total Output Energy` | kWh delivered to all outputs | ✅ Yes |
| `AC Input Energy` | kWh from AC input only | ❌ No (enable in entities) |
| `Power Difference` | Net power flow (W) | ✅ Yes |

---

## 🔧 What Changed from beta8

### Added
- Automatic energy sensor integration
- Power difference sensor for Energy Dashboard
- Recorder exclusions for performance
- Base classes for energy sensors (`EcoFlowIntegralEnergySensor`, `EcoFlowPowerDifferenceSensor`)

### Technical
- Uses Home Assistant's `IntegrationSensor` helper
- Energy sensors use "left" integration method
- 60-second max sub-interval for accuracy
- Auto-tracks power sensor state changes

---

## 🚀 Upgrade Path

### From beta7 or earlier:
1. Update to beta9
2. Restart Home Assistant
3. Check logs for MQTT connection success
4. Enable AC Input Energy sensor if needed (optional)
5. Configure Energy Dashboard

### From beta8:
1. Update to beta9
2. Restart Home Assistant  
3. Energy sensors appear automatically
4. Configure Energy Dashboard to use new sensors

---

## 📝 Notes

- Energy sensors are **diagnostic entities** (hidden by default in UI)
- Find them in **Settings** → **Devices & Services** → **EcoFlow Delta Pro 3** → **Entities**
- Total Input/Output energy sensors are enabled by default
- AC Input energy sensor is disabled (enable if needed)
- Power Difference sensor works immediately after setup

---

**Thanks to `tolwi/hassio-ecoflow-cloud` for inspiration!** 🙏

