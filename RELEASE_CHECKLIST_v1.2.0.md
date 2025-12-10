# Release Checklist v1.2.0

## ✅ Pre-Release Checklist

### Code Changes
- [x] Updated `manifest.json` version to 1.2.0
- [x] Updated `CHANGELOG.md` with v1.2.0 changes
- [x] Updated `README.md` with new features
- [x] Created `RELEASE_NOTES_v1.2.0.md`
- [x] Created `DELTA_PRO_3_API_MAPPING.md` documentation
- [x] Created `examples/template_sensors.yaml`
- [x] Updated `const.py` with real Delta Pro 3 sensors (40+)
- [x] Added binary sensors (13)
- [x] Added switches (3)
- [x] Added numbers (7)

### Testing
- [x] Tested with real Delta Pro 3 device (SN: MR51ZES5PG860274)
- [x] Verified all API endpoints
- [x] Tested API authentication
- [x] Saved real API response (`api_response_MR51ZES5PG860274.json`)
- [x] Documented MQTT vs REST API comparison
- [x] Created template sensors for estimated cycles

### Documentation
- [x] Complete API mapping with examples
- [x] MQTT vs REST API analysis
- [x] Cycles explanation and workarounds
- [x] Template sensors examples
- [x] Installation instructions
- [x] Configuration guide
- [x] Troubleshooting section

## 📦 Release Steps

### 1. Create Release Archive

```bash
# Option 1: Using Python script
python create_release_zip.py 1.2.0

# Option 2: Using PowerShell
cd custom_components
Compress-Archive -Path "ecoflow_api" -DestinationPath "../ecoflow-api-v1.2.0.zip" -Force

# Option 3: Manual
# Zip the custom_components/ecoflow_api folder
# Name it: ecoflow-api-v1.2.0.zip
```

### 2. Verify Archive Contents

The ZIP should contain:
```
ecoflow_api/
├── __init__.py
├── api.py
├── binary_sensor.py
├── config_flow.py
├── const.py
├── coordinator.py
├── devices/
│   ├── __init__.py
│   └── delta_pro_3/
│       ├── __init__.py
│       └── const.py
├── diagnostics.py
├── entity.py
├── manifest.json (version: 1.2.0)
├── number.py
├── select.py
├── sensor.py
├── strings.json
├── switch.py
└── translations/
    ├── en.json
    └── uk.json
```

### 3. Create GitHub Release

1. Go to: https://github.com/TarasKhust/hassio-ecoflow-api/releases/new

2. **Tag**: `v1.2.0`

3. **Title**: `v1.2.0 - Complete Delta Pro 3 Support`

4. **Description**: Copy from `RELEASE_NOTES_v1.2.0.md`

5. **Attach Files**:
   - `ecoflow-api-v1.2.0.zip`
   - `DELTA_PRO_3_API_MAPPING.md` (optional, for reference)
   - `examples/template_sensors.yaml` (optional)

6. **Check**: ✅ Set as the latest release

7. Click **Publish release**

### 4. Update HACS

HACS will automatically detect the new release from GitHub tags.

Users can update via:
- HACS → Integrations → EcoFlow API → Update

### 5. Announce Release

Post in:
- [ ] Home Assistant Community Forum
- [ ] Reddit r/homeassistant
- [ ] GitHub Discussions

## 📋 Release Notes Summary

**What's New in v1.2.0:**

🎉 **Complete Delta Pro 3 Support**
- 40+ sensors based on real device data
- 13 binary sensors for status monitoring
- 10 control entities (switches & numbers)
- Full API documentation with examples

📚 **Documentation**
- Complete API mapping (DELTA_PRO_3_API_MAPPING.md)
- MQTT vs REST API comparison
- Template sensors for estimated cycles
- Ready-to-use Home Assistant examples

🧪 **Testing**
- Verified with real Delta Pro 3 device
- All sensors tested and documented
- API responses saved for reference

⚠️ **Important Notes**
- Cycles not available in REST API (MQTT only)
- Template sensor provided for estimation
- REST API recommended for stability

## 🎯 Post-Release

- [ ] Monitor GitHub Issues for problems
- [ ] Update documentation if needed
- [ ] Respond to user questions
- [ ] Plan next release features

## 📊 Version History

- **v1.2.0** (2025-12-10) - Complete Delta Pro 3 support with real data
- **v1.1.4** (2024-12-10) - Binary sensors fixes
- **v1.1.3** (2024-12-09) - Timestamp sensor fixes
- **v1.1.2** (2024-12-09) - Signature generation fixes
- **v1.1.1** (2024-12-09) - PUT request fixes
- **v1.1.0** (2024-12-09) - Code structure improvements
- **v1.0.8** (2024-12-09) - Modular device structure
- **v1.0.7** (2024-12-08) - 85+ sensors added
- **v1.0.0** (2024-12-01) - Initial release

## 🚀 Next Steps

After releasing v1.2.0, consider:

1. **More Devices**
   - Delta 2 support
   - Delta 2 Max support
   - River series support

2. **Features**
   - Energy dashboard integration
   - Advanced automations examples
   - Optional MQTT support

3. **Documentation**
   - Video tutorials
   - More language translations
   - Integration with other HA components

4. **Community**
   - Gather feedback
   - Fix reported issues
   - Implement feature requests

---

**Ready to release!** 🎉

All code changes are complete and tested. Just need to:
1. Create the ZIP archive
2. Create GitHub release
3. Announce to community



