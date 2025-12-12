# EcoFlow API v1.4.0-beta3 - Timezone Fixes & Code Cleanup

## 🔧 Bug Fixes

### UTC Timezone Offset Display
- **Fixed**: Added unit "min" (minutes) to UTC Timezone Offset sensor
- **Details**: Sensor now displays "200 min" instead of just "200" for better clarity
- **Note**: Value 200 minutes = UTC+3:20 (as returned by device API)

## 🧹 Code Cleanup

### Removed Duplicate Binary Sensor
- **Removed**: Duplicate `device_sleeping` binary sensor (was redundant)
- **Reason**: Already have `sensor.dev_sleep_state` that shows the same data
- **Usage**: Use `sensor.ecoflow_delta_pro_3_device_sleep_state` (0 = awake, != 0 = sleeping)

### Fixed Ukrainian Translations
- **Fixed**: Corrected switch translations in `uk.json`
- **Changes**:
  - Replaced obsolete keys (`ac_out_state`, `dc_out_state`, etc.)
  - Added missing translations for all switches:
    - `ac_hv_out`, `ac_lv_out`, `dc_12v_out`
    - `x_boost`, `beeper`, `ac_energy_saving`
    - `generator_auto_start`, `gfci`

## Technical Changes

- Improved `utc_timezone` sensor formatting with proper unit display
- Cleaned up binary sensor definitions to avoid redundancy
- Synchronized translations between English and Ukrainian for switches
- All translations now match actual entity keys used in code

---

**Full Changelog**: v1.4.0-beta2...v1.4.0-beta3

