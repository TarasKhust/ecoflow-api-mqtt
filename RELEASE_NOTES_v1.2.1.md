# Release v1.2.1 - Dynamic Update Interval Control

## 🎉 What's New

### Dynamic Update Interval Control
Now you can change how often the integration polls the EcoFlow API without restarting Home Assistant!

**New Entity**: `select.ecoflow_delta_pro_3_update_interval`

**Available Options**:
- 🚀 **5 seconds (Fast)** - For real-time monitoring
- ⚡ **10 seconds** - Quick updates
- ✅ **15 seconds (Recommended)** - Balanced (default)
- 🐢 **30 seconds** - Reduced API calls
- 🕐 **60 seconds (Slow)** - Minimal API usage

**Features**:
- ✅ Change interval on the fly through Home Assistant UI
- ✅ No restart required - changes apply immediately
- ✅ Settings persist after restart
- ✅ Available in both select entity and Settings → Configure

## 🐛 Bug Fixes

### Fixed OptionsFlow Error
- Fixed "Config flow could not be loaded: 500 Internal Server Error" when clicking Settings → Configure
- Removed unused imports causing initialization errors
- Simplified options handling logic

## 📦 Installation

### Via HACS (Recommended)
1. Go to HACS → Integrations
2. Find "EcoFlow API"
3. Click "Update" or "Redownload"
4. Restart Home Assistant

### Manual Installation
1. Download `ecoflow_api.zip` from this release
2. Extract to `custom_components/ecoflow_api/`
3. Restart Home Assistant

## 🎯 How to Use

### Method 1: Select Entity (Recommended)
1. Go to Settings → Devices & Services → EcoFlow API
2. Click on your device
3. Find `select.ecoflow_delta_pro_3_update_interval`
4. Choose your preferred interval
5. Changes apply immediately!

### Method 2: OptionsFlow
1. Go to Settings → Devices & Services → EcoFlow API
2. Click the ⚙️ (Configure) button
3. Select your preferred update interval
4. Click Submit

## 📊 Technical Details

**Modified Files**:
- `config_flow.py` - Fixed OptionsFlow error
- `select.py` - Added update_interval select entity with local setting support
- `coordinator.py` - Added `async_set_update_interval()` method

**Commits**:
- `2ce3c9b` - fix: Fix OptionsFlow error in config_flow
- `2b20545` - feat: Add dynamic update interval select entity

## 🔗 Links

- [Full Changelog](CHANGELOG.md)
- [Documentation](README.md)
- [Issue Tracker](https://github.com/TarasKhust/hassio-ecoflow-api/issues)
- [Linear Task MON-11](https://linear.app/moneymanagerapp/issue/MON-11)

## 💬 Feedback

If you encounter any issues or have suggestions, please [open an issue](https://github.com/TarasKhust/hassio-ecoflow-api/issues).

---

**Full Changelog**: https://github.com/TarasKhust/hassio-ecoflow-api/compare/v1.2.0...v1.2.1

