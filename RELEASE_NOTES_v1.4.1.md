# v1.4.1 - Debug Logging on Demand

## 🎛️ Control Your Logs!

Now you can **enable detailed debug logs only when you need them** - perfect for troubleshooting!

---

## ✅ What's New

### Default Behavior (Clean Logs):
```log
✅ REST API connected for device 0274 (hybrid mode, update interval: 15s)
✅ MQTT connected to broker for device 0274
```

Only connection events, warnings, and errors.

---

### With Debug Enabled (Full Details):

Add to `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.ecoflow_api: debug
```

**Restart Home Assistant**, and you'll see:
```log
🔄 [10:05:39] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=16.2s, mqtt=ON)
✅ [10:05:39] REST update for 0274: received 160 fields, 4 changed
📊 [10:05:39] Changed fields (4 total):
   • bmsDsgRemTime: 29037 → 29308
   • cmsDsgRemTime: 29037 → 29308
🔀 [10:05:39] Merged data: REST=160 + MQTT=250 = Total=269 fields

⚡ [10:05:35] MQTT message for 0274: 2 fields updated
   Fields: bmsDsgRemTime, cmsDsgRemTime
```

---

## 🎯 When to Use Debug Mode

| Scenario | Logger Config | What You See |
|----------|--------------|--------------|
| **Daily use** | None | ✅ Connections, ⚠️ warnings, 🔴 errors |
| **Troubleshooting** | `debug` | 🔄 REST updates, ⚡ MQTT messages, 📊 field changes |
| **Performance check** | `debug` | Timing info, merge stats, intervals |

---

## 📋 How to Enable Debug Logging

### Step 1: Edit configuration.yaml

Add this section:
```yaml
logger:
  logs:
    custom_components.ecoflow_api: debug
```

### Step 2: Restart Home Assistant

**Settings → System → Restart**

### Step 3: View Logs

**Settings → System → Logs**

You'll see detailed debug information!

---

## 🔇 How to Disable Debug Logging

### Option 1: Remove from configuration.yaml

Delete or comment out:
```yaml
# logger:
#   logs:
#     custom_components.ecoflow_api: debug
```

Restart HA.

### Option 2: Change level to warning

```yaml
logger:
  logs:
    custom_components.ecoflow_api: warning  # Only errors/warnings
```

Restart HA.

---

## 🎨 Debug Log Features

### REST Updates:
- Trigger time with actual interval
- Fields received vs changed
- Changed fields list (max 10 shown)
- MQTT status

### MQTT Messages:
- Timestamp of each message
- Number of fields updated
- Field names list (max 10 shown)

### Data Merge:
- REST field count
- MQTT field count
- Total unique fields after merge

---

## 📊 Example Debug Session

```log
10:05:39 🔄 REST UPDATE TRIGGERED for 0274 (interval=15s, actual=16.2s, mqtt=ON)
10:05:41 ✅ REST update for 0274: 160 fields, 4 changed
10:05:41 📊 Changed fields (4 total):
10:05:41    • bmsDsgRemTime: 29037 → 29308
10:05:41    • cmsDsgRemTime: 29037 → 29308
10:05:41    • quota_cloud_ts: 2025-12-13 00:05:22 → 2025-12-13 00:05:37
10:05:41    • plugInInfo4p82Resv.resvInfo: [1120135739...] → [1120135575...]
10:05:41 🔀 Merged data for 0274: REST=160 + MQTT=250 = Total=269 unique fields

10:05:35 ⚡ MQTT message for 0274: 2 fields updated
10:05:35    Fields: bmsDsgRemTime, cmsDsgRemTime

10:05:38 ⚡ MQTT message for 0274: 1 fields updated
10:05:38    Fields: plugInInfo4p82Resv
```

---

## 🚀 Migration from v1.4.0

**No changes needed!** Just update and:

- **Default:** Clean logs (same as v1.4.0)
- **Optional:** Add logger config for debug details

---

## 📦 Installation

### Via HACS:
1. HACS → Integrations → EcoFlow API
2. Update to **v1.4.1**
3. Restart Home Assistant

### Manual:
Download: `ecoflow-api-v1.4.1.zip`

---

## 🎯 Benefits

| Aspect | v1.4.0 | v1.4.1 |
|--------|--------|--------|
| **Clean Logs** | ✅ Yes | ✅ Yes |
| **Debug On Demand** | ❌ No | ✅ Yes |
| **Easy Toggle** | ❌ N/A | ✅ Config only |
| **No Restart for Toggle** | ❌ N/A | ⚠️ Restart needed |

---

## 💡 Pro Tips

1. **Daily Use:** Don't add logger config - keep logs clean
2. **Debugging:** Add `debug` level - see everything
3. **After Fix:** Remove `debug` - back to clean logs

---

**Enjoy flexible logging! 🎉**

