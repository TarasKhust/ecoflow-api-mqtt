# 🚨 v1.4.0-beta8 - Critical Fix: REST Polling Blocked by MQTT

## 🐛 Critical Bug Found!

### Problem
**REST polling was completely blocked when MQTT was active!**

**Why this happened:**
1. MQTT updates data every 2-3 seconds via `async_set_updated_data()`
2. Home Assistant's `DataUpdateCoordinator` sees data is fresh
3. **Scheduled REST refresh is skipped** (thinks: "data already updated")
4. REST `_async_update_data()` **NEVER gets called**
5. No REST logs appear: `🔄 REST UPDATE TRIGGERED` missing

**Result:**
- ✅ MQTT worked perfectly (every 2-3 sec)
- ❌ REST never polled (even though configured for 15s)
- ❌ No REST logs
- ❌ Missing REST-only fields (if any)
- ❌ No fallback if MQTT fails

## ✅ Solution

Added **independent timer** for REST updates that runs separately from `DataUpdateCoordinator`:

```python
# New timer in hybrid_coordinator.py
self._rest_update_timer = self.hass.loop.call_later(
    self.update_interval_seconds,
    lambda: asyncio.create_task(self._do_rest_update())
)
```

**Now:**
- 🔄 **REST polls every N seconds** (independent timer)
- ⚡ **MQTT updates every 2-3 sec** (realtime)
- 📊 **Both work simultaneously**
- 🔁 **REST continues even if MQTT fails**

## 📊 What You'll See Now

### Before (beta7):
```log
⚡ [09:43:03] MQTT message: 79 fields
⚡ [09:43:05] MQTT message: 2 fields
⚡ [09:43:08] MQTT message: 2 fields
⚡ [09:43:12] MQTT message: 2 fields
... only MQTT, NO REST logs!
```

### After (beta8):
```log
🔄 [09:43:00] REST UPDATE TRIGGERED (interval=15s, mqtt=ON)
✅ [09:43:00] REST update: received 160 fields, 5 changed
🔀 [09:43:00] Merged: REST=160 + MQTT=0 = Total=160 fields

⚡ [09:43:03] MQTT message: 79 fields
⚡ [09:43:05] MQTT message: 2 fields  
⚡ [09:43:08] MQTT message: 2 fields

🔄 [09:43:15] REST UPDATE TRIGGERED (interval=15s, mqtt=ON)
✅ [09:43:15] REST update: received 160 fields, 2 changed
🔀 [09:43:15] Merged: REST=160 + MQTT=250 = Total=269 fields
```

## 🎯 Impact

**This was a CRITICAL bug** affecting all users with MQTT enabled!

- REST polling was silently disabled
- Only MQTT data was used
- No logging for REST (users couldn't see the problem)
- No fallback if MQTT disconnected

## 📥 Installation

### Through HACS:
1. HACS → Integrations → EcoFlow API
2. Update → **v1.4.0-beta8**
3. Restart Home Assistant
4. **Check logs** - you should now see `🔄 REST UPDATE TRIGGERED` every 15s!

### Manual:
1. Download: `ecoflow-api-v1.4.0-beta8.zip`
2. Extract to `/config/custom_components/ecoflow_api/`
3. Restart Home Assistant

## ✅ Verification

After installing beta8:

1. **Settings → System → Logs**
2. Wait 30 seconds
3. Search for: `REST UPDATE TRIGGERED`
4. **You MUST see REST logs now!**

Expected pattern:
- REST update every 15 seconds (or your configured interval)
- MQTT messages every 2-3 seconds
- Both working together

---

**HUGE thanks to @TarasKhust for reporting missing REST logs!** 🙏

This bug would have gone unnoticed without careful log monitoring!

---

## 📝 Changelog

### Fixed
- **Critical:** REST polling now works independently of MQTT updates
- REST timer no longer blocked by frequent MQTT data
- REST logs now appear as expected

### Added
- Independent timer for REST updates (`_rest_update_timer`)
- Proper cleanup of timer on shutdown
- Ensured REST + MQTT work simultaneously

### Technical
- Override default DataUpdateCoordinator behavior
- Manual scheduling of REST updates
- Separation of MQTT (realtime) and REST (periodic) update paths

