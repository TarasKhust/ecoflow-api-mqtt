# EcoFlow API v1.4.0-beta4 - Enhanced REST Update Logging

## 🆕 New Features

### Detailed Field Change Logging
- **Added**: REST update logging now shows which fields actually changed
- **Details**: 
  - Logs count of changed fields in summary message
  - Shows detailed list of first 20 changed fields with old → new values
  - Helps diagnose which data is actually updating from REST API
  - Prevents log spam by limiting to 20 fields and truncating long values

### Example Log Output:
```
✅ REST update for MR51ZES5PG860274: received 160 fields (15 changed)
📊 Changed fields for MR51ZES5PG860274: bmsBattSoc: 98.1 → 98.3; powGetAcIn: 1200 → 1250; ...
```

## Technical Changes

- Enhanced `_async_update_data()` in `hybrid_coordinator.py`
- Compares new REST data with previous data (`self._last_data`)
- Formats values for readability (truncates to 30 chars, shows None for null values)
- Only logs changes when fields actually differ

## Benefits

- **Better Diagnostics**: See exactly what data updates from REST API
- **Performance Insights**: Understand which fields change frequently vs rarely
- **Debugging**: Easier to spot stale data or missing updates
- **Log Clarity**: Focused on actual changes, not all data every time

---

**Full Changelog**: v1.4.0-beta3...v1.4.0-beta4

