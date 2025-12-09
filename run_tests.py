#!/usr/bin/env python3
"""Simple test runner without pytest dependency."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print("🧪 EcoFlow API Integration Tests")
print("="*70)
print()

# Test 1: Module imports
print("📦 Test 1: Module Imports")
print("-"*70)
try:
    from custom_components.ecoflow_api.const import (
        DOMAIN,
        DEFAULT_UPDATE_INTERVAL,
        UPDATE_INTERVAL_OPTIONS,
    )
    print("✅ Main constants imported successfully")
    print(f"   DOMAIN: {DOMAIN}")
    print(f"   DEFAULT_UPDATE_INTERVAL: {DEFAULT_UPDATE_INTERVAL} seconds")
except Exception as e:
    print(f"❌ Failed to import main constants: {e}")
    sys.exit(1)

try:
    from custom_components.ecoflow_api.devices.delta_pro_3 import (
        DEVICE_TYPE,
        DEVICE_MODEL,
        COMMAND_BASE,
    )
    print("✅ Delta Pro 3 constants imported successfully")
    print(f"   DEVICE_TYPE: {DEVICE_TYPE}")
    print(f"   DEVICE_MODEL: {DEVICE_MODEL}")
except Exception as e:
    print(f"❌ Failed to import Delta Pro 3 constants: {e}")
    sys.exit(1)

try:
    from custom_components.ecoflow_api import api
    print("✅ API module imported successfully")
except Exception as e:
    print(f"❌ Failed to import API module: {e}")
    sys.exit(1)

try:
    from custom_components.ecoflow_api import coordinator
    print("✅ Coordinator module imported successfully")
except Exception as e:
    print(f"❌ Failed to import coordinator module: {e}")
    sys.exit(1)

print()

# Test 2: Constants validation
print("🔍 Test 2: Constants Validation")
print("-"*70)

tests_passed = 0
tests_failed = 0

# Test domain
if DOMAIN == "ecoflow_api":
    print("✅ DOMAIN is correct")
    tests_passed += 1
else:
    print(f"❌ DOMAIN is wrong: {DOMAIN}")
    tests_failed += 1

# Test default update interval
if DEFAULT_UPDATE_INTERVAL == 15:
    print("✅ DEFAULT_UPDATE_INTERVAL is correct (15 seconds)")
    tests_passed += 1
else:
    print(f"❌ DEFAULT_UPDATE_INTERVAL is wrong: {DEFAULT_UPDATE_INTERVAL}")
    tests_failed += 1

# Test update interval options
expected_intervals = [5, 10, 15, 30, 60]
actual_intervals = list(UPDATE_INTERVAL_OPTIONS.values())
if all(interval in actual_intervals for interval in expected_intervals):
    print(f"✅ UPDATE_INTERVAL_OPTIONS contains all expected values: {expected_intervals}")
    tests_passed += 1
else:
    print(f"❌ UPDATE_INTERVAL_OPTIONS missing values. Expected: {expected_intervals}, Got: {actual_intervals}")
    tests_failed += 1

# Test device type
if DEVICE_TYPE == "DELTA Pro 3":
    print("✅ DEVICE_TYPE is correct")
    tests_passed += 1
else:
    print(f"❌ DEVICE_TYPE is wrong: {DEVICE_TYPE}")
    tests_failed += 1

# Test command base structure
required_command_keys = ["cmdId", "dirDest", "dirSrc", "cmdFunc", "dest", "needAck"]
if all(key in COMMAND_BASE for key in required_command_keys):
    print(f"✅ COMMAND_BASE has all required keys: {required_command_keys}")
    tests_passed += 1
else:
    missing_keys = [key for key in required_command_keys if key not in COMMAND_BASE]
    print(f"❌ COMMAND_BASE missing keys: {missing_keys}")
    tests_failed += 1

# Test command base values
expected_values = {
    "cmdId": 17,
    "dirDest": 1,
    "dirSrc": 1,
    "cmdFunc": 254,
    "dest": 2,
    "needAck": True,
}
all_correct = True
for key, expected_value in expected_values.items():
    if COMMAND_BASE.get(key) != expected_value:
        print(f"❌ COMMAND_BASE[{key}] is wrong. Expected: {expected_value}, Got: {COMMAND_BASE.get(key)}")
        all_correct = False
        tests_failed += 1

if all_correct:
    print("✅ COMMAND_BASE values are all correct")
    tests_passed += 1

print()

# Test 3: API client structure
print("🔧 Test 3: API Client Structure")
print("-"*70)

try:
    from custom_components.ecoflow_api.api import EcoFlowApiClient
    print("✅ EcoFlowApiClient class imported successfully")
    
    # Check methods exist
    required_methods = [
        "_generate_nonce",
        "_flatten_params",
        "_sort_and_concat_params",
        "get_device_list",
        "get_device_quota",
        "set_device_quota",
    ]
    
    missing_methods = []
    for method in required_methods:
        if not hasattr(EcoFlowApiClient, method):
            missing_methods.append(method)
    
    if not missing_methods:
        print(f"✅ All required methods exist: {required_methods}")
        tests_passed += 1
    else:
        print(f"❌ Missing methods: {missing_methods}")
        tests_failed += 1
        
except Exception as e:
    print(f"❌ Failed to test API client: {e}")
    tests_failed += 1

print()

# Summary
print("="*70)
print("📊 Test Summary")
print("="*70)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Total:  {tests_passed + tests_failed}")
print()

if tests_failed == 0:
    print("🎉 All tests passed!")
    sys.exit(0)
else:
    print("⚠️  Some tests failed!")
    sys.exit(1)

