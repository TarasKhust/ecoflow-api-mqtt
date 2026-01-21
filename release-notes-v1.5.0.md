## 🚀 What's New

### ✨ New Features

#### Extra Battery Sensors for Delta Pro 3

- **SOC** - State of Charge (%)
- **SOH** - State of Health (%)
- **Design Capacity** - Original battery capacity (Ah)
- **Full Capacity** - Current full capacity (Ah)
- **Remain Capacity** - Remaining capacity (Ah)

Data is decoded from `plugInInfo4p8xResv.resvInfo` array:

- SOC/SOH decoded as IEEE 754 float
- Capacity values converted from mAh to Ah
- Automatic fallback: uses port 4p82 as primary, falls back to 4p81

#### River 3 Plus Device Support

- Full support using same API as River 3
- All sensors, switches, numbers, selects, binary sensors

#### Region Selection

- **EU** - api-e.ecoflow.com
- **US** - api.ecoflow.com
- Select region during setup

### 🐛 Fixes

- Fixed sensor naming - descriptive names now shown in Home Assistant
- Fixed Extra Battery sensors showing Unknown when battery connected to port 2

### 📚 Documentation

- Updated README with new devices
- Added region support documentation
- Updated supported devices table

### 🧪 Testing

- Tested with real Delta Pro 3 device
- Verified Extra Battery data decoding
- Confirmed River 3 Plus compatibility

---

**Full Changelog**: https://github.com/TarasKhust/ecoflow-api-mqtt/compare/v1.4.2...v1.5.0
