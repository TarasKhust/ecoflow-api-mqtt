# 🔧 EcoFlow API Integration v1.1.3 - Timestamp Fix

Виправлення помилки timestamp сенсорів.

## 🐛 Що виправлено

### Timestamp Sensor Error

**Проблема:** При використанні контролів (number/switch/select) з'являлася помилка:
```
Failed to perform the action number/set_value. 
Invalid datetime: sensor.ecoflow_delta_pro_3_cloud_timestamp has timestamp 
device class but provides state 2025-12-10 04:33:33:<class 'str'> 
resulting in ''str' object has no attribute 'tzinfo''
```

**Причина:** Timestamp сенсори повертали строку замість datetime об'єкта.

**Рішення:** 
- Timestamp значення тепер правильно конвертуються в timezone-aware datetime об'єкти
- Додано обробку помилок парсингу з логуванням
- Використовується UTC timezone якщо timezone не вказано

## ✅ Що працює

Версія 1.1.3 містить всі виправлення з 1.1.2:

### ✅ Device Controls (Протестовано!)
- **Number entities**: AC Charging Power, charge levels, brightness, тощо
- **Switch entities**: AC/DC outputs, X-Boost, Beeper, тощо
- **Select entities**: Standby times, output frequency, тощо

### ✅ Sensors
- Всі сенсори даних (battery, power, temperature, тощо)
- **Timestamp сенсори** тепер працюють правильно

## 📦 Оновлення

### Через HACS:
1. Відкрийте **HACS** → **Integrations**
2. Знайдіть **EcoFlow API** 
3. Натисніть **Update** (версія 1.1.3)
4. **Перезапустіть Home Assistant**

### Вручну:
1. Завантажте: [ecoflow-api-v1.1.3.zip](https://github.com/TarasKhust/hassio-ecoflow-api/releases/download/v1.1.3/ecoflow-api-v1.1.3.zip)
2. Замініть файли в `config/custom_components/ecoflow_api/`
3. Перезапустіть Home Assistant

## 📝 Changelog

- v1.1.3: Fix timestamp sensor datetime conversion
- v1.1.2: Working signature fix (tested on real device)
- v1.1.1: Initial signature fix attempt
- v1.1.0: Code improvements and translations

## 🐛 Повідомити про помилку

Знайшли баг? [Створіть issue](https://github.com/TarasKhust/hassio-ecoflow-api/issues/new)

---

Made with ❤️ in Ukraine 🇺🇦
