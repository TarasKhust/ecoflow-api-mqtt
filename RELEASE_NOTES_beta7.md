# 🐛 v1.4.0-beta7 - Bugfix: Change Detection Edge Cases

## Fixed Issues

### Bug 1: Missing Removed Fields Detection
**Problem:** Code only checked fields in new data, missing removed fields.

**Example:**
```python
Previous: {"battery": 85, "temp": 25, "power": 100}
Current:  {"battery": 84, "power": 95}
❌ Old: Reports "2 changed" (battery, power) - misses that temp was removed
✅ New: Reports "3 changed" (battery, power, temp→None)
```

### Bug 2: Empty Dict Handling
**Problem:** Used `if self._last_data:` which treats `{}` as `False`.

**Example:**
```python
Update 1: API returns {} (empty response)
         _last_data = {}  # stored
         
Update 2: API returns {"battery": 85, "temp": 25}
         if self._last_data:  # ❌ False! {} is falsy
             # This code doesn't run!
         ❌ Old: "0 changed" 
         ✅ New: "2 changed" (battery, temp appeared)
```

## Technical Changes

```python
# Old (buggy)
if self._last_data:
    for key, new_value in data.items():
        if old_value != new_value:
            changed_fields.append(...)

# New (fixed)
if self._last_data is not None:
    # Check changed/new fields
    for key, new_value in data.items():
        if old_value != new_value:
            changed_fields.append(...)
    
    # Check removed fields
    for key in self._last_data:
        if key not in data:
            changed_fields.append((key, old_val, None))
```

## Impact

These edge cases could cause:
- 🔴 Missed change notifications
- 🔴 Incorrect "0 changed" in logs when fields actually changed
- 🔴 Hidden device issues (removed sensors not detected)

## Files Changed

- `coordinator.py` - REST-only mode
- `hybrid_coordinator.py` - Hybrid mode (REST + MQTT)

## Installation

### Through HACS:
1. HACS → Integrations → EcoFlow API → Update
2. Select v1.4.0-beta7
3. Restart Home Assistant

### Manual:
1. Download: `ecoflow-api-v1.4.0-beta7.zip`
2. Extract to `/config/custom_components/ecoflow_api/`
3. Restart Home Assistant

---

**Thanks @TarasKhust for spotting these issues!** 🙏

