# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0-beta15] - 2025-12-11

### Fixed
- 🔄 **MQTT Thread Safety** - Fixed TypeError in MQTT callback
  - Replaced `async_create_task` with `async_add_job` for proper thread-safe async calls
  - `async_add_job` is the standard Home Assistant way to call async functions from other threads
  - Fixes `TypeError: a coroutine was expected, got None` error
  - Ensures MQTT updates properly synchronize with Home Assistant entities

## [1.3.0-beta14] - 2025-12-11

### Fixed
- 🔄 **MQTT Data Updates** - Fixed dashboard not updating in real-time
  - Fixed MQTT callback thread safety issue
  - Properly schedules coordinator updates from MQTT thread to HA event loop
  - Entities now receive updates immediately when MQTT data arrives
  - Fixes issue where dashboard only updated when official app was opened
  - Uses `call_soon_threadsafe` for proper async function scheduling

### Changed
- 📊 **Automation Time Formatting** - Improved time display in notifications
  - Changed time format from decimal hours (e.g., `2.4h`) to readable format (e.g., `2h 40m`)
  - Battery level percentages now rounded to whole numbers (e.g., `75%` instead of `75.48937%`)
  - Applied to all three automations: Smart Charging, Power Switch, Battery Alerts

## [1.3.0-beta13] - 2025-12-11

### Added
- 🔄 **Device Wake-Up Mechanism** - Fixes data update issues
  - Automatically sends wake-up request before fetching data
  - Smart wake-up: skips if MQTT is active (device already awake)
  - Fixes issue where data doesn't update until official app is opened
  - Uses REST API wake-up with 0.5s delay for device activation
  - Hybrid mode: leverages MQTT connection to keep device active

### Fixed
- 📊 **Timestamp Sensors** - Improved handling of timestamp data
  - Added support for numeric Unix timestamps (milliseconds and seconds)
  - Automatically converts numeric timestamps to datetime objects
  - Fixes `quota_cloud_ts` and `quota_device_ts` sensors

### Changed
- 📝 **Repository Cleanup** - Non-commercial license and better organization
  - Changed license to Non-Commercial License
  - Renamed repository to `ecoflow-api-mqtt`
  - Added direct HACS installation link
  - Added Hybrid Mode documentation
  - Removed development helper scripts from repository
  - Cleaned up `.gitignore` rules

### Home Assistant Automations (in `automations/` folder)
- ⚡ **Smart Charging** - Adaptive charging based on power outage schedule
  - Adjusts charging power based on Yasno power outage predictions
  - Calculates optimal power to reach 100% before outage
  - Adaptive polling intervals (5/10/15 min based on urgency)
  - Shows outage type and duration in notifications
- 🔌 **Power Switch** - Combined grid/battery switch notifications
  - Single automation for both grid and battery mode
  - Shows charge/discharge time and power consumption
- 🔋 **Battery Alerts** - Combined battery status notifications
  - Low battery (<20%), Critical (<10%), High temp (>40°C), Full charge
  - Smart notifications with relevant information per alert type

## [1.3.0-beta12] - 2025-12-10

### Fixed
- 🔋 **Battery Cycles Sensor** - Added missing "key" field for cycles mapping
  - MQTT sends `cycles` field (not `bmsCycles`)
  - Now correctly maps `cycles` from MQTT to Battery Cycles sensor
  - Cycles sensor now shows data from MQTT (e.g., 26, 30 cycles detected)

### Note
Delta Pro 3 has multiple batteries (extra batteries), each with its own cycles count:
- Battery 1: `bmsSn: MR52Z1S5PG8R0374` - cycles: 26
- Battery 2: `bmsSn: MR51PA08PG830151` - cycles: 30
Currently shows the last received cycles value. Future enhancement: separate sensors per battery.

## [1.3.0-beta11] - 2025-12-10

### Fixed
- 🐛 **Thread Safety** - Fix async_write_ha_state called from wrong thread
  - MQTT callback runs in different thread than Home Assistant event loop
  - Use hass.async_add_job() to schedule updates in correct event loop
  - Prevents Home Assistant crashes and data corruption
  - Fixes "calls async_write_ha_state from a thread other than the event loop" warning

## [1.3.0-beta10] - 2025-12-10

### Fixed
- 🐛 **MQTT Message Parsing** - Handle MQTT messages without 'params' wrapper
  - EcoFlow MQTT sends data directly (not wrapped in params)
  - Now correctly processes both wrapped and unwrapped formats
  - Fixes "Quota message missing 'params'" warnings in logs
  - MQTT real-time updates now working correctly! ✅

## [1.3.0-beta9] - 2025-12-10

### Added
- ⚡ **Automatic Energy Sensors** - Full integration with Home Assistant Energy Dashboard
  - Automatically creates kWh sensors from power (W) sensors
  - Total Input Energy sensor (enabled by default)
  - Total Output Energy sensor (enabled by default)
  - AC Input Energy sensor (disabled by default)
  - Compatible with HA Energy Dashboard for tracking consumption and generation
- 📊 **Power Difference Sensor** - Shows net power flow (Input - Output)
  - Positive value = charging/receiving power
  - Negative value = discharging/consuming power
  - Useful for Energy Dashboard "Now" tab
- 🗄️ **Recorder Exclusions** - Database optimization
  - Technical attributes excluded from database history
  - Reduces database size and improves performance
  - Excludes: mqtt_connected, last_update_time, device_info, etc.

### Changed
- 📦 **Energy Dashboard Integration** - Power sensors now automatically integrate to energy
- 🔧 **Sensor Architecture** - Added base classes for energy and power difference sensors

## [1.3.0-beta8] - 2025-12-10

### Fixed
- 🔐 **MQTT Authentication** - Now automatically fetches `certificateAccount` and `certificatePassword` from EcoFlow API
  - Added `get_mqtt_credentials()` method to retrieve proper MQTT credentials
  - MQTT topics now use correct `certificateAccount` instead of email
  - Fixes "Connection Refused - not authorized (code 5)" error
- 📡 **MQTT Topics** - Proper certificateAccount used in all MQTT topics
  - `/open/{certificateAccount}/{sn}/quota` - Uses API-provided certificateAccount
  - `/open/{certificateAccount}/{sn}/status` - Device online/offline status
  - `/open/{certificateAccount}/{sn}/set` - Send commands
  - `/open/{certificateAccount}/{sn}/set_reply` - Command responses

### Changed
- 🔧 **MQTT Setup** - Integration now fetches MQTT credentials automatically on startup
- 📝 **Options Flow** - MQTT username/password fields now optional (auto-fetched from API)

## [1.3.0-beta7] - 2025-12-10

### Added
- 📊 **Complete GetAllQuotaResponse field mapping** - All fields from API documentation now mapped
  - Device status fields: errcode, devSleepState, devStandbyTime, bleStandbyTime
  - Battery status: bmsChgDsgState, cmsChgDsgState, cmsBmsRunState
  - Generator settings: cmsOilSelfStart, cmsOilOffSoc, cmsOilOnSoc
  - Power flow: powGet5p8, powGet4p81, powGet4p82, powGetAcLvTt30Out
  - Plug-in info: All plugInInfo* numeric/string fields (50+ fields)
  - Flow info: All flowInfo* enum sensors (17 fields)
  - Settings: fastChargeSwitch, energyBackupEn, llcHvLvFlag, acLvAlwaysOn, acHvAlwaysOn, etc.
- 🔧 **Fixed MQTT topics** - Corrected topic format from `/app/...` to `/open/{certificateAccount}/{sn}/...`
  - `/open/{certificateAccount}/{sn}/quota` - Device quota updates
  - `/open/{certificateAccount}/{sn}/status` - Device online/offline status
  - `/open/{certificateAccount}/{sn}/set` - Send commands
  - `/open/{certificateAccount}/{sn}/set_reply` - Command responses
- 📡 **Improved MQTT message handling** - Proper parsing for quota, status, and set_reply topics

### Changed
- 🔄 **MQTT client** - Updated to use correct EcoFlow MQTT protocol format
- 📝 **Documentation** - Updated MQTT protocol comments with correct topic structure

## [1.3.0-beta1] - 2025-12-10

### Added
- 🚀 **Hybrid REST API + MQTT Support** - Best of both worlds!
  - ⚡ **Real-time updates via MQTT** - Instant sensor updates without polling
  - 🔧 **Device control via REST API** - Reliable command execution
  - 🔄 **Automatic fallback** - Seamlessly falls back to REST if MQTT unavailable
  - 📊 **Battery Cycles sensor** - Now available via MQTT (`bmsCycles`)
  - 🎛️ **MQTT configuration** - Enable/disable MQTT through Settings → Configure
- 📡 **MQTT Client** - Full WebSocket-based MQTT implementation
  - Broker: `mqtt.ecoflow.com:8883` (TLS)
  - Real-time device status updates
  - Automatic reconnection
- 🔀 **Hybrid Coordinator** - Intelligent data merging
  - MQTT data priority (more real-time)
  - REST API fallback for reliability
  - Reduced REST polling when MQTT active (4x less frequent)

### Changed
- 📦 **Dependencies** - Added `paho-mqtt>=1.6.1` for MQTT support
- 🔧 **Coordinator** - Can now be hybrid (REST+MQTT) or REST-only
- ⚙️ **Configuration** - MQTT settings in OptionsFlow (Settings → Configure)

### Technical Details
- ✅ **New files**: `mqtt_client.py`, `hybrid_coordinator.py`
- ✅ **MQTT authentication**: Uses EcoFlow account credentials
- ✅ **Connection modes**: `hybrid`, `mqtt_standby`, `rest_only`
- ✅ **Graceful degradation**: Works without MQTT if not configured

### Beta Notes
- ⚠️ **Beta release** - Please test and report issues
- 🧪 **MQTT is optional** - Integration works fine without it
- 📝 **Feedback needed**: MQTT connection stability, data accuracy
- 🔍 **Known limitations**: MQTT credentials must be EcoFlow account (email/password)

## [1.2.1] - 2025-12-10

### Added
- 🎛️ **Dynamic Update Interval Control** - New select entity for runtime interval changes
  - `select.ecoflow_delta_pro_3_update_interval` - Change polling frequency on the fly
  - Options: 5s (Fast), 10s, 15s (Recommended), 30s, 60s (Slow)
  - Changes apply immediately without restart
  - Settings persist after Home Assistant restart
- ⚙️ **OptionsFlow Configuration** - Configure update interval through Settings → Configure

### Fixed
- 🐛 **OptionsFlow 500 error** - Fixed "Config flow could not be loaded" error
  - Removed unused `UPDATE_INTERVAL_OPTIONS` import
  - Simplified options handling logic

### Technical Details
- ✅ **Coordinator enhancement** - Added `async_set_update_interval()` method
- ✅ **Local settings support** - Select platform now supports both device and local settings
- ✅ **Config persistence** - Interval changes saved to config entry options

## [1.2.0] - 2025-12-10

### Added
- 🎉 **Complete Delta Pro 3 support based on real API data**
  - 📊 **40+ sensors** - All available metrics from actual Delta Pro 3 device
  - 🔋 **Battery sensors** - BMS and CMS battery data (SOC, SOH, remaining time, capacity)
  - ⚡ **Power sensors** - Total input/output, AC, Solar (HV/LV), DC outputs (12V/24V), USB-C, QC USB
  - 🌡️ **Temperature sensors** - Min/Max cell and MOSFET temperatures
  - ⚙️ **Settings sensors** - Standby times, LCD brightness, frequency
  - 🔌 **13 binary sensors** - Charging status (AC, Solar, batteries), X-Boost, GFCI, etc.
  - 🎛️ **3 switches** - X-Boost, Beep, AC Energy Saving
  - 🔢 **7 number controls** - AC charging power, charge levels, standby times, LCD brightness
- 📚 **Comprehensive documentation**
  - 📖 **DELTA_PRO_3_API_MAPPING.md** - Complete API reference with real data examples
  - 🔍 **MQTT vs REST API comparison** - Detailed analysis and recommendations
  - 📝 **Cycles explanation** - Why cycles are not available in REST API and alternatives
- 🧪 **Template sensors examples** - Ready-to-use Home Assistant templates for:
  - 🔄 Estimated cycles calculation based on SOH
  - 💚 Battery health status
  - ⚡ Charging status with multiple sources
  - 📊 Net power flow
  - ⏱️ Runtime and charge time estimates
  - 🚨 Low battery and high temperature alerts
- 🧪 **API testing tools** - Standalone test script to verify API responses

### Changed
- 🔄 **Sensor definitions updated** - All sensors now use actual API keys from real Delta Pro 3
- 📊 **Sensor naming** - More descriptive names (e.g., "Battery Level (BMS)" vs "Battery Level (CMS)")
- 📝 **Documentation improvements** - Based on actual device testing (SN: MR51ZES5PG860274)

### Technical Details
- ✅ **Tested with real device** - DELTA Pro 3 (online, SOH 100%, 8192Wh capacity)
- 📡 **API endpoint verified** - `/iot-open/sign/device/quota/all`
- 🔐 **Authentication working** - EcoFlow Developer API (api-e.ecoflow.com)
- 🌍 **Timezone support** - UTC timezone handling (Europe/Kiev tested)

### Notes
- ⚠️ **Cycles not available** - REST API does not provide cycle count (only available via MQTT)
- 💡 **Alternative solution** - Template sensor for estimated cycles based on SOH included
- 📖 **Why REST API?** - More stable and officially supported than MQTT (see documentation)

## [1.1.4] - 2024-12-10

### Fixed
- 🐛 **Binary sensors fixed** - Corrected API key mappings for all binary sensors
- 🔋 **Charging/Discharging detection** - Now uses correct `powInSumW` and `powOutSumW` keys
- 🔌 **AC Input Connected** - Fixed to use `powGetAcIn` instead of non-existent `acInPower`
- ☀️ **Solar Connected** - Fixed to use `powGetPvH` instead of non-existent `solarInPower`
- 🪫 **Battery Low/Full** - Fixed to use `bmsBattSoc` instead of non-existent `soc`
- 🌡️ **Over Temperature** - Fixed to use `bmsMaxCellTemp` instead of non-existent `bmsTemp`
- ⚡ **Threshold adjustment** - Changed charging/discharging detection threshold from 0W to 10W to avoid false positives

## [1.1.3] - 2024-12-09

### Fixed
- 🐛 **Timestamp sensor error** - Fixed "str object has no attribute 'tzinfo'" error for timestamp sensors
- 🕐 **Datetime conversion** - Timestamp sensors now correctly return timezone-aware datetime objects

## [1.1.2] - 2024-12-09

### Fixed
- 🐛 **ACTUALLY fixed signature generation for PUT requests** - Now correctly includes flattened JSON body parameters in signature calculation, as required by EcoFlow API documentation
- 🔧 **Boolean conversion** - Boolean values now converted to lowercase strings (true/false) in signature
- ✅ **Tested and verified** - AC Charging Power control tested successfully (1200W → 1500W)

### Added
- 🧪 **Test script** - Added `test_set_ac_power.py` for manual testing of device controls

## [1.1.1] - 2024-12-09

### Fixed
- 🐛 **Critical fix: Signature generation for PUT requests** - Fixed "signature is wrong" error (code 8521) when controlling devices. PUT requests now correctly generate signature only from auth parameters, not from JSON body content.

## [1.1.0] - 2024-12-09

### Added
- 🏗️ **Improved code structure** - Better organization of entity management
- 📝 **Enhanced translations** - Updated English and Ukrainian translations
- 🧪 **Better test coverage** - Improved test structure and documentation
- 🔧 **Configuration improvements** - Enhanced config flow and diagnostics

### Changed
- 🔄 **Entity management** - Improved binary sensor, number, select, and switch entities
- 📊 **Coordinator updates** - Better device state handling
- 📖 **Code quality** - Refactored code for better maintainability

### Fixed
- 🐛 **Minor bug fixes** - Various small improvements and fixes

## [1.0.8] - 2024-12-09

### Added
- 🏗️ **Modular device structure** - Device-specific logic organized in `devices/` subdirectories
- 🧪 **Comprehensive test suite** - Unit tests for API client, config flow, and integration structure
- 📊 **Structure validation script** - Quick check for file structure without dependencies (`check_structure.py`)
- 📚 **Testing documentation** - Detailed testing guide in `tests/README.md`
- ⚙️ **Configurable update interval** - Users can now choose update frequency (5/10/15/30/60 seconds)
- 🔄 **Immediate state refresh** - After control actions, state updates after 2 seconds
- 📝 **Changelog** - This file to track all changes

### Changed
- 🔧 **Default update interval** - Changed from 30s to 15s for better responsiveness
- 📁 **Project structure** - Device-specific constants moved to `devices/delta_pro_3/`
- 📖 **README updates** - Added testing section, options configuration, and updated troubleshooting

### Fixed
- 🐛 **Nonce generation** - Corrected to generate 6-digit nonce (was 16 characters)
- 🔐 **API signature** - Fixed signature generation to match EcoFlow API requirements
- ⏱️ **Timestamp issues** - Ensured fresh timestamps for each API request

## [1.0.7] - 2024-12-08

### Added
- 📊 **85+ sensors** - All available data points from Delta Pro 3 API
- 🎛️ **23 control entities** - 8 switches, 12 numbers, 4 selects
- 🇺🇦 **Ukrainian translations** - Full localization for all entities

### Changed
- 🔄 **Sensor definitions** - Based on real API response keys
- 🛠️ **Control commands** - Updated to match EcoFlow API documentation

## [1.0.6] - 2024-12-07

### Fixed
- 🔧 **Content-Type header** - Conditionally added based on HTTP method (GET vs POST/PUT)
- 🌐 **API base URL** - Corrected to `https://api-e.ecoflow.com`

## [1.0.5] - 2024-12-06

### Fixed
- 🔐 **GET request parameters** - Parameters now in URL query string, not request body
- 📝 **Signature generation** - Parameter order corrected (request params first, then auth params)

## [1.0.4] - 2024-12-05

### Fixed
- 🔐 **API authentication** - Initial fix for signature generation

## [1.0.3] - 2024-12-04

### Added
- 🔍 **HACS validation** - Repository topics for HACS discovery

### Fixed
- 📦 **HACS download** - Removed `zip_release` from `hacs.json`

## [1.0.2] - 2024-12-03

### Added
- ✨ **Manual device entry** - Users can manually enter device serial number and type
- 📋 **Device selection menu** - Choose between auto-discovery and manual entry

### Fixed
- 🔧 **Config flow** - Improved error handling and user experience

## [1.0.1] - 2024-12-02

### Added
- 🔧 **Config flow improvements** - Better device discovery

### Fixed
- 🐛 **Initial setup issues** - Various bug fixes

## [1.0.0] - 2024-12-01

### Added
- 🎉 **Initial release**
- ✅ **Delta Pro 3 support** - Full support for EcoFlow Delta Pro 3
- 🔌 **Basic sensors** - Battery level, power, temperature, etc.
- 🎛️ **Basic controls** - AC/DC output, charging power, X-Boost
- 🔧 **Config flow** - Easy setup through Home Assistant UI
- 📡 **Official API** - Uses EcoFlow Developer API
- 🇺🇦 **Ukrainian localization** - Translations for Ukrainian language

---

## Legend

- 🎉 Major features
- ✅ Features
- 🔧 Improvements
- 🐛 Bug fixes
- 🔐 Security
- 📝 Documentation
- 🧪 Testing
- 🇺🇦 Localization
- 📊 Sensors
- 🎛️ Controls
- 🏗️ Architecture
- 🌐 API


