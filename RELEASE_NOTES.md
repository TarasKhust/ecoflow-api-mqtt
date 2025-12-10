# 🔧 EcoFlow API Integration v1.1.4 - Binary Sensors Fix

Виправлення всіх binary sensors - тепер працюють правильно!

## 🐛 Що виправлено

### Binary Sensors Fixed

**Проблема:** Всі binary sensors не працювали через неправильні API ключі:
- Charging/Discharging detection використовував неіснуючі ключі
- AC Input Connected шукав `acInPower` замість `powGetAcIn`
- Solar Connected шукав `solarInPower` замість `powGetPvH`
- Battery Low/Full використовували `soc` замість `bmsBattSoc`
- Over Temperature використовував `bmsTemp` замість `bmsMaxCellTemp`

**Рішення:** 
- 🔋 **Charging Detection**: Тепер використовує `powInSumW` (сумарна вхідна потужність)
- 🔌 **Discharging Detection**: Тепер використовує `powOutSumW` (сумарна вихідна потужність)
- ⚡ **Threshold**: Змінено з 0W на 10W для уникнення хибних спрацювань
- 🔌 **AC Input Connected**: Виправлено на `powGetAcIn`
- ☀️ **Solar Connected**: Виправлено на `powGetPvH`
- 🪫 **Battery Low/Full**: Виправлено на `bmsBattSoc`
- 🌡️ **Over Temperature**: Виправлено на `bmsMaxCellTemp`

## ✅ Що працює

### ✅ Binary Sensors (Виправлено!)
- **Charging** - показує чи заряджається пристрій (>10W вхідної потужності)
- **Discharging** - показує чи розряджається пристрій (>10W вихідної потужності)
- **AC Input Connected** - показує чи підключено AC вхід
- **Solar Connected** - показує чи підключені сонячні панелі
- **Battery Low** - попередження при низькому заряді (<20%)
- **Battery Full** - показує повний заряд (>95%)
- **Over Temperature** - попередження при перегріві (>50°C)

### ✅ Device Controls (Протестовано!)
- **Number entities**: AC Charging Power, charge levels, brightness, тощо
- **Switch entities**: AC/DC outputs, X-Boost, Beeper, тощо
- **Select entities**: Standby times, output frequency, тощо

### ✅ Sensors
- Всі сенсори даних (battery, power, temperature, тощо)
- Timestamp сенсори працюють правильно

## 📦 Оновлення

### Через HACS:
1. Відкрийте **HACS** → **Integrations**
2. Знайдіть **EcoFlow API** 
3. Натисніть **Update** (версія 1.1.4)
4. **Перезапустіть Home Assistant**

### Вручну:
1. Завантажте: [ecoflow-api-v1.1.4.zip](https://github.com/TarasKhust/hassio-ecoflow-api/releases/download/v1.1.4/ecoflow-api-v1.1.4.zip)
2. Замініть файли в `config/custom_components/ecoflow_api/`
3. Перезапустіть Home Assistant

## 📝 Changelog

- v1.1.4: Fix all binary sensors with correct API keys
- v1.1.3: Fix timestamp sensor datetime conversion
- v1.1.2: Working signature fix (tested on real device)
- v1.1.1: Initial signature fix attempt
- v1.1.0: Code improvements and translations

## 🐛 Повідомити про помилку

Знайшли баг? [Створіть issue](https://github.com/TarasKhust/hassio-ecoflow-api/issues/new)

---

Made with ❤️ in Ukraine 🇺🇦
