# v1.4.0 - Smart Logging & Improved Stability

## 🎯 Highlights

This release focuses on **clean, informative logging** and **improved stability** for daily use.

### ✅ What's New

**Smart Logging:**
- Logs only important events (connection, errors, shutdown)
- No more log spam from routine operations
- Clear status messages for troubleshooting

**Improved Stability:**
- Fixed REST polling blocked by MQTT updates
- Better error handling for edge cases
- Improved change detection logic

---

## 📋 Detailed Changes

### 🔇 Clean Logs (No More Spam!)

**Before (v1.3.x):**
```log
🔄 [10:05:39] REST UPDATE TRIGGERED for 0274...
✅ [10:05:39] REST update: 160 fields, 4 changed
📊 [10:05:39] Changed fields:
   • bmsDsgRemTime: 29037 → 29308
   • cmsDsgRemTime: 29037 → 29308
⚡ [10:05:35] MQTT message: 2 fields updated
⚡ [10:05:38] MQTT message: 1 fields updated
... (every 15 seconds + every MQTT message)
```

**Now (v1.4.0):**
```log
✅ REST API connected for device 0274 (hybrid mode, update interval: 15s)
✅ MQTT connected to broker for device 0274 (hybrid mode: MQTT + REST every 15s)

... (silence - everything working smoothly) ...

🔴 REST API error for 0274: timeout
⚠️ MQTT connection lost, retrying...
🔵 Shutting down EcoFlow API for device 0274
```

**You'll only see logs when:**
- ✅ Initial connection successful (INFO)
- ⚠️ Connection problems (WARNING)  
- 🔴 API errors (ERROR)
- 🔵 System shutdown (INFO)

---

### 🐛 Bug Fixes

1. **REST Polling Blocked by MQTT** (Critical)
   - **Problem:** Frequent MQTT updates prevented REST polling from occurring
   - **Fix:** Independent REST timer ensures polling at configured interval
   - **Impact:** Hybrid mode now works correctly with both MQTT and REST

2. **Change Detection Edge Cases**
   - **Problem:** Removed fields not detected; empty data dict handling incorrect
   - **Fix:** Improved comparison logic for all scenarios
   - **Impact:** More accurate data updates

3. **Interval Configuration**
   - **Problem:** REST interval automatically doubled when MQTT connected
   - **Fix:** Interval now strictly follows configuration
   - **Impact:** 15s config = 15s polling (not 30s or 60s)

---

## 📊 What You'll See in Logs

### On Startup (REST-only mode):
```log
✅ REST API connected for device 0274 (REST-only mode, update interval: 15s)
```

### On Startup (Hybrid mode):
```log
✅ REST API connected for device 0274 (hybrid mode, update interval: 15s)
✅ MQTT connected to broker for device 0274 (hybrid mode: MQTT + REST every 15s)
```

### On MQTT Failure:
```log
⚠️ MQTT connection failed for device 0274, using REST API only
```

### On API Error:
```log
🔴 REST API error for 0274: Connection timeout
```

### On Shutdown:
```log
🔵 Shutting down EcoFlow API for device 0274
```

---

## 🚀 Migration from v1.3.x

### Automatic Migration

No configuration changes needed! The integration will:
- Continue using your existing settings
- Apply new smart logging automatically
- Work exactly as before (but quieter)

### Optional: Remove Logger Config

If you have this in `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.ecoflow_api: debug  # or warning
```

You can **remove it** - it's no longer needed. Smart logging is now built-in!

---

## 🎯 Benefits

| Aspect | Before (v1.3.x) | Now (v1.4.0) |
|--------|----------------|--------------|
| **Log Volume** | High (every update) | Low (events only) |
| **Troubleshooting** | Difficult (too much info) | Easy (clear messages) |
| **REST Polling** | Blocked by MQTT | Independent timer ✅ |
| **Interval Control** | Auto-adjusted | Configuration-based ✅ |
| **Change Detection** | Basic | Comprehensive ✅ |

---

## 📦 Installation

### Via HACS (Recommended):
1. HACS → Integrations → EcoFlow API
2. Update to **v1.4.0**
3. Restart Home Assistant

### Manual:
1. Download `ecoflow-api-v1.4.0.zip`
2. Extract to `custom_components/ecoflow_api/`
3. Restart Home Assistant

---

## 🙏 Acknowledgments

Special thanks to the community for:
- Detailed bug reports
- Testing beta releases
- Feature suggestions

Your feedback made this release possible!

---

## 🔗 Links

- [GitHub Repository](https://github.com/TarasKhust/ecoflow-api-mqtt)
- [HACS Store](https://github.com/hacs/integration)
- [Documentation](https://github.com/TarasKhust/ecoflow-api-mqtt#readme)

---

**Enjoy clean logs and stable operation!** 🎉

