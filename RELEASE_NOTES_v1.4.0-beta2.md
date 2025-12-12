# EcoFlow API v1.4.0-beta2 - Cloud Timestamp Fix

## 🔧 Bug Fixes

### Cloud Timestamp Timezone Fix
- **Fixed**: Cloud Timestamp sensor now correctly displays local time instead of UTC
- **Problem**: Timestamp was showing UTC time (22:17) instead of local timezone (16:18) in Ukraine (UTC+2)
- **Solution**: Improved timestamp parsing to ensure proper UTC conversion and timezone-aware datetime handling
- **Details**: Added explicit timezone checks and conversions to ensure Home Assistant correctly converts UTC timestamps to local timezone for display

## Technical Changes

- Enhanced timestamp parsing in `sensor.py` to properly handle UTC timestamps
- Added explicit timezone checks to ensure timestamps are timezone-aware
- Improved datetime conversion for `SensorDeviceClass.TIMESTAMP` sensors
- Proper handling of both string and numeric timestamp formats from API

## Testing

Please verify that:
- ✅ Cloud Timestamp sensor shows correct local time
- ✅ Device Timestamp sensor shows correct local time (if applicable)
- ✅ All timestamp sensors update correctly

---

**Full Changelog**: v1.4.0-beta1...v1.4.0-beta2

