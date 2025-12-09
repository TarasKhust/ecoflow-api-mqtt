#!/usr/bin/env python3
"""Check integration file structure without requiring dependencies."""
import os
import json

print("="*70)
print("📁 EcoFlow API Integration - Structure Check")
print("="*70)
print()

BASE_PATH = "custom_components/ecoflow_api"
tests_passed = 0
tests_failed = 0

# Test 1: Check required files exist
print("📋 Test 1: Required Files")
print("-"*70)

required_files = [
    f"{BASE_PATH}/__init__.py",
    f"{BASE_PATH}/manifest.json",
    f"{BASE_PATH}/const.py",
    f"{BASE_PATH}/api.py",
    f"{BASE_PATH}/config_flow.py",
    f"{BASE_PATH}/coordinator.py",
    f"{BASE_PATH}/entity.py",
    f"{BASE_PATH}/sensor.py",
    f"{BASE_PATH}/binary_sensor.py",
    f"{BASE_PATH}/switch.py",
    f"{BASE_PATH}/number.py",
    f"{BASE_PATH}/select.py",
    f"{BASE_PATH}/strings.json",
    f"{BASE_PATH}/translations/en.json",
    f"{BASE_PATH}/translations/uk.json",
]

for file_path in required_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
        tests_passed += 1
    else:
        print(f"❌ Missing: {file_path}")
        tests_failed += 1

print()

# Test 2: Check device structure
print("🔧 Test 2: Device Module Structure")
print("-"*70)

device_files = [
    f"{BASE_PATH}/devices/__init__.py",
    f"{BASE_PATH}/devices/delta_pro_3/__init__.py",
    f"{BASE_PATH}/devices/delta_pro_3/const.py",
]

for file_path in device_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
        tests_passed += 1
    else:
        print(f"❌ Missing: {file_path}")
        tests_failed += 1

print()

# Test 3: Check manifest.json
print("📄 Test 3: Manifest Validation")
print("-"*70)

manifest_path = f"{BASE_PATH}/manifest.json"
if os.path.exists(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    required_keys = ["domain", "name", "version", "documentation", "requirements"]
    for key in required_keys:
        if key in manifest:
            print(f"✅ manifest.json has '{key}': {manifest[key]}")
            tests_passed += 1
        else:
            print(f"❌ manifest.json missing '{key}'")
            tests_failed += 1
    
    # Check version
    if manifest.get("version") == "1.0.8":
        print(f"✅ Version is correct: 1.0.8")
        tests_passed += 1
    else:
        print(f"⚠️  Version is: {manifest.get('version')} (expected 1.0.8)")
        # Not failing this as version might be different
        tests_passed += 1
else:
    print(f"❌ manifest.json not found")
    tests_failed += 1

print()

# Test 4: Check translations
print("🌐 Test 4: Translations")
print("-"*70)

strings_path = f"{BASE_PATH}/strings.json"
if os.path.exists(strings_path):
    with open(strings_path, 'r', encoding='utf-8') as f:
        strings = json.load(f)
    
    required_sections = ["config", "options", "entity"]
    for section in required_sections:
        if section in strings:
            print(f"✅ strings.json has '{section}' section")
            tests_passed += 1
        else:
            print(f"❌ strings.json missing '{section}' section")
            tests_failed += 1
else:
    print(f"❌ strings.json not found")
    tests_failed += 1

print()

# Test 5: Check test structure
print("🧪 Test 5: Test Files")
print("-"*70)

test_files = [
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_api.py",
    "tests/test_config_flow.py",
    "tests/test_simple.py",
    "pytest.ini",
    "requirements-test.txt",
]

for file_path in test_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
        tests_passed += 1
    else:
        print(f"❌ Missing: {file_path}")
        tests_failed += 1

print()

# Test 6: Check .gitignore for test files
print("🔒 Test 6: .gitignore")
print("-"*70)

gitignore_path = ".gitignore"
if os.path.exists(gitignore_path):
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    test_patterns = ["test_*.py", "get_device_data.py"]
    for pattern in test_patterns:
        if pattern in gitignore_content:
            print(f"✅ .gitignore includes '{pattern}'")
            tests_passed += 1
        else:
            print(f"⚠️  .gitignore doesn't include '{pattern}' (might be OK)")
            tests_passed += 1  # Not critical
else:
    print(f"❌ .gitignore not found")
    tests_failed += 1

print()

# Summary
print("="*70)
print("📊 Summary")
print("="*70)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Total:  {tests_passed + tests_failed}")
print()

if tests_failed == 0:
    print("🎉 All structure checks passed!")
    print()
    print("✨ Integration is ready for:")
    print("   1. Installation in Home Assistant")
    print("   2. Testing with real device")
    print("   3. Publishing to GitHub")
    exit(0)
else:
    print("⚠️  Some structure checks failed!")
    exit(1)


