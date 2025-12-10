# v1.3.0-beta8 - MQTT Authentication Fix

## 🔐 Fixed MQTT Authentication Issue

This release fixes the **"Connection Refused - not authorized (code 5)"** MQTT error by implementing proper credential fetching from EcoFlow API.

### Key Changes

**🔧 Automatic MQTT Credentials:**
- Integration now automatically fetches `certificateAccount` and `certificatePassword` from EcoFlow API endpoint `/iot-open/sign/certification`
- No need to manually enter MQTT username/password in Options
- MQTT credentials are obtained using your access_key/secret_key

**📡 Correct MQTT Topics:**
- Topics now use proper `certificateAccount` (not email) as required by EcoFlow MQTT protocol
- `/open/{certificateAccount}/{sn}/quota` - Device data updates
- `/open/{certificateAccount}/{sn}/status` - Online/offline status
- `/open/{certificateAccount}/{sn}/set` - Command sending
- `/open/{certificateAccount}/{sn}/set_reply` - Command responses

**🐛 Bug Fixes:**
- Fixed code 5 "Not authorized" error during MQTT connection
- MQTT client now uses API-provided credentials instead of user email/password
- Improved logging to show which certificateAccount is being used

### How It Works

1. **Enable MQTT** in integration Options (gear icon)
2. Integration automatically calls EcoFlow API to get MQTT credentials
3. `certificateAccount` and `certificatePassword` are used for MQTT authentication
4. MQTT topics use the correct `certificateAccount` format

### Migration from beta7

If you had MQTT enabled in beta7:
1. Update to beta8
2. Restart Home Assistant
3. MQTT should connect automatically using API-fetched credentials
4. Check logs for `✅ Connected to MQTT broker` message

### What to Expect

After update, you should see in logs:
```
MQTT enabled, fetching MQTT credentials from API...
Successfully obtained MQTT credentials from API
MQTT client initialized - username: ..., certificateAccount: ..., device_sn: ...
✅ Connected to MQTT broker for device ...
```

### If MQTT Still Doesn't Connect

Check logs for:
- `Error fetching MQTT credentials` - API call failed
- MQTT topics format in logs should show proper certificateAccount
- Connection error codes and troubleshooting info

---

**Implementation based on:** `tolwi/hassio-ecoflow-cloud` integration analysis - thanks to the community! 🙏

