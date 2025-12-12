# v1.4.0-beta10 - Controllable Verbose Logging

## 🎛️ New Feature: Verbose Logging Control

**Problem solved:** Detailed logs were always enabled, causing log spam even when not debugging.

**Solution:** Added **Verbose Logging** option in integration settings!

### ✅ How It Works

**Default (Verbose Logging OFF):**
- ✅ Clean logs - only errors and warnings
- ✅ No log spam
- ✅ Perfect for daily use

**When Debugging (Verbose Logging ON):**
- 🔄 REST update notifications with timing
- ⚡ MQTT message details with field lists
- 📊 Changed fields with old/new values
- 🔀 Data merge statistics

### 📥 How to Use

1. **Settings → Devices & Services → EcoFlow API**
2. Click **Configure** (⚙️)
3. Toggle **"Verbose Logging (Debug Mode)"**
4. Save

**No restart needed!** Logging changes immediately.

---

## 🐛 Fixes from beta9

- Fixed REST timer task creation using `hass.async_create_task`
- Better error handling in scheduled updates
- Added debug logging for timer execution

---

## 📋 What You'll See

### With Verbose Logging OFF (default):
```log
2025-12-12 10:00:00 INFO [ecoflow_api] Integration started
```

### With Verbose Logging ON:
```log
🔄 [10:05:39] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=16.2s, mqtt=ON)
🌐 [10:05:39] Fetching REST data for 0274...
✅ [10:05:39] REST update for 0274: received 160 fields, 4 changed
📊 [10:05:39] Changed fields (4 total):
   • bmsDsgRemTime: 29037 → 29308
   • cmsDsgRemTime: 29037 → 29308
🔀 [10:05:39] Merged: REST=160 + MQTT=250 = Total=269 fields

⚡ [10:05:35] MQTT message for 0274: 2 fields updated
   Fields: bmsDsgRemTime, cmsDsgRemTime
```

---

## 🎯 Perfect for:

- ✅ **Daily use**: Keep verbose logging OFF for clean logs
- 🐛 **Debugging**: Turn ON to see detailed update info
- 📊 **Monitoring**: Check REST/MQTT timing and data flow
- 🔍 **Troubleshooting**: Identify which fields are changing

---

## 📦 Installation

**Via HACS:**
1. HACS → Integrations → EcoFlow API
2. ⋮ → Redownload → v1.4.0-beta10
3. Restart Home Assistant
4. Configure verbose logging as needed

**Manual:**
Download `ecoflow-api-v1.4.0-beta10.zip` and extract to `custom_components/`

---

## 🚀 Coming Next

After testing beta10, we'll prepare **v1.4.0 stable** release with all improvements!

### Timeline:
- beta10 ← **You are here** 🎯
- Stable 1.4.0 ← Soon! 🚀

