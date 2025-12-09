# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.8] - 2024-12-09

### Added
- 🏗️ **Modular device structure** - Device-specific logic organized in `devices/` subdirectories
- 🧪 **Comprehensive test suite** - Unit tests for API client, config flow, and integration structure
- 📊 **Structure validation script** - Quick check for file structure without dependencies (`check_structure.py`)
- 📚 **Testing documentation** - Detailed testing guide in `tests/README.md`
- ⚙️ **Configurable update interval** - Users can now choose update frequency (5/10/15/30/60 seconds)
- 🔄 **Immediate state refresh** - After control actions, state updates after 2 seconds
- 📝 **Changelog** - This file to track all changes

### Changed
- 🔧 **Default update interval** - Changed from 30s to 15s for better responsiveness
- 📁 **Project structure** - Device-specific constants moved to `devices/delta_pro_3/`
- 📖 **README updates** - Added testing section, options configuration, and updated troubleshooting

### Fixed
- 🐛 **Nonce generation** - Corrected to generate 6-digit nonce (was 16 characters)
- 🔐 **API signature** - Fixed signature generation to match EcoFlow API requirements
- ⏱️ **Timestamp issues** - Ensured fresh timestamps for each API request

## [1.0.7] - 2024-12-08

### Added
- 📊 **85+ sensors** - All available data points from Delta Pro 3 API
- 🎛️ **23 control entities** - 8 switches, 12 numbers, 4 selects
- 🇺🇦 **Ukrainian translations** - Full localization for all entities

### Changed
- 🔄 **Sensor definitions** - Based on real API response keys
- 🛠️ **Control commands** - Updated to match EcoFlow API documentation

## [1.0.6] - 2024-12-07

### Fixed
- 🔧 **Content-Type header** - Conditionally added based on HTTP method (GET vs POST/PUT)
- 🌐 **API base URL** - Corrected to `https://api-e.ecoflow.com`

## [1.0.5] - 2024-12-06

### Fixed
- 🔐 **GET request parameters** - Parameters now in URL query string, not request body
- 📝 **Signature generation** - Parameter order corrected (request params first, then auth params)

## [1.0.4] - 2024-12-05

### Fixed
- 🔐 **API authentication** - Initial fix for signature generation

## [1.0.3] - 2024-12-04

### Added
- 🔍 **HACS validation** - Repository topics for HACS discovery

### Fixed
- 📦 **HACS download** - Removed `zip_release` from `hacs.json`

## [1.0.2] - 2024-12-03

### Added
- ✨ **Manual device entry** - Users can manually enter device serial number and type
- 📋 **Device selection menu** - Choose between auto-discovery and manual entry

### Fixed
- 🔧 **Config flow** - Improved error handling and user experience

## [1.0.1] - 2024-12-02

### Added
- 🔧 **Config flow improvements** - Better device discovery

### Fixed
- 🐛 **Initial setup issues** - Various bug fixes

## [1.0.0] - 2024-12-01

### Added
- 🎉 **Initial release**
- ✅ **Delta Pro 3 support** - Full support for EcoFlow Delta Pro 3
- 🔌 **Basic sensors** - Battery level, power, temperature, etc.
- 🎛️ **Basic controls** - AC/DC output, charging power, X-Boost
- 🔧 **Config flow** - Easy setup through Home Assistant UI
- 📡 **Official API** - Uses EcoFlow Developer API
- 🇺🇦 **Ukrainian localization** - Translations for Ukrainian language

---

## Legend

- 🎉 Major features
- ✅ Features
- 🔧 Improvements
- 🐛 Bug fixes
- 🔐 Security
- 📝 Documentation
- 🧪 Testing
- 🇺🇦 Localization
- 📊 Sensors
- 🎛️ Controls
- 🏗️ Architecture
- 🌐 API


