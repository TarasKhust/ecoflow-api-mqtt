# 🚀 Beta Release v1.5.0-beta.2 - Delta Pro, River 3 & Delta 3 Plus Support

**Бета-реліз з підтримкою нових пристроїв EcoFlow Delta Pro, River 3 та Delta 3 Plus!**

## ⚠️ Beta Notice

Це бета-версія для тестування нових пристроїв. Будь ласка, повідомляйте про будь-які проблеми в [Issues](https://github.com/TarasKhust/ecoflow-api-mqtt/issues).

## ✨ Нові пристрої

### 🔋 Delta Pro (Original)

Повна підтримка EcoFlow Delta Pro з HTTP API:

**Sensors (70+):**

- BMS: SOC, SOH, Voltage, Current, Temperature, Capacity, Cycles
- Inverter: AC Input/Output Power, Voltage, Current, Frequency
- MPPT: Solar Input Power, Voltage, Current
- PD: USB, Type-C, 12V/24V DC Power
- EMS: Charge/Discharge Time, LCD SOC

**Switches (5):**

- AC Output, X-Boost, Car Charger, Beeper, Bypass AC Auto

**Numbers (10):**

- Charge/Discharge Limits, AC Charging Power
- Standby Times (Device, AC, Screen)
- Generator Controls (Hybrid Mode SOC, Care Mode)

**Selects (2):**

- PV Charging Type (Auto/MPPT/Adapter)
- AC Output Frequency (50Hz/60Hz)

**Binary Sensors (10):**

- AC/Solar/Car Input Connected
- Charging/Discharging Status
- Battery Low/Full, X-Boost/Beeper Enabled

### 🌊 River 3

Повна підтримка EcoFlow River 3:

**Sensors (40+):**

- Battery: SOC, SOH, Voltage, Current, Temperature
- CMS: Overall Battery Status
- Power: Total In/Out, AC, PV, USB, Type-C, 12V
- AC: Input/Output Voltage, Current, Frequency

**Switches (6):**

- AC Output, 12V DC Output, X-Boost
- Beeper, Backup Reserve, Power Off Memory

**Numbers (8):**

- Charge/Discharge Limits
- AC Charging Power (50-305W)
- Device/AC/Screen Standby Times
- PV Charging Current

**Selects (2):**

- Update Interval
- DC Charging Mode (Auto/Solar/Car)

**Binary Sensors (10):**

- AC/Solar Connected, Charging/Discharging
- AC/DC Output Enabled, Battery Low/Full
- X-Boost/Beeper Enabled

### ⚡ Delta 3 Plus

Повна підтримка EcoFlow Delta 3 Plus:

**Sensors (50+):**

- Battery: SOC, SOH, Voltage, Current, Temperature, Capacity
- CMS: Overall Battery Status, Total Energy
- Power: Total In/Out, AC, PV1/PV2, USB, Type-C, 12V, DC Port
- AC: Input/Output Voltage, Current, Frequency
- Dual PV Input support (PV1 + PV2)

**Switches (6):**

- AC Output, 12V DC Output, USB Output
- X-Boost, Beeper, Smart Generator Auto Start

**Numbers (10):**

- Charge/Discharge Limits
- AC Charging Power (100-1500W)
- Device/AC/DC/Screen Standby Times
- LCD Brightness
- Generator Start/Stop SOC

**Selects (2):**

- Update Interval
- AC Charging Mode (Fast/Custom/Silent)

**Binary Sensors (13):**

- AC/PV1/PV2 Connected, Charging/Discharging
- AC/DC/USB Output Enabled, Battery Low/Full
- X-Boost/Beeper/Backup Reserve Enabled
- AC/DC Output Enabled, Battery Low/Full
- X-Boost/Beeper Enabled

## 🔧 Технічні деталі

### Delta Pro API Format

```json
{
  "sn": "DEVICE_SN",
  "cmdSet": 32,
  "id": <command_id>,
  "params": { ... }
}
```

### River 3 / Delta Pro 3 API Format

```json
{
  "sn": "DEVICE_SN",
  "cmdId": 17,
  "cmdFunc": 254,
  "params": { ... }
}
```

## 📦 Встановлення

### Через HACS (Custom Repository)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add: `https://github.com/TarasKhust/ecoflow-api-mqtt`
3. Category: Integration
4. Download version `1.5.0-beta.1`
5. Restart Home Assistant

### Або вручну

1. Завантажити ZIP з [Releases](https://github.com/TarasKhust/ecoflow-api-mqtt/releases/tag/v1.5.0-beta.1)
2. Розпакувати в `custom_components/ecoflow_api/`
3. Restart Home Assistant

## 🧪 Тестування

### Delta Pro

1. Додайте пристрій через Configuration → Integrations → EcoFlow API
2. Виберіть тип пристрою "Delta Pro"
3. Перевірте всі entities в Developer Tools → States

### River 3

1. Додайте пристрій через Configuration → Integrations → EcoFlow API
2. Виберіть тип пристрою "River 3"
3. Перевірте всі entities в Developer Tools → States

## 📝 Зворотній зв'язок

Будь ласка, повідомляйте про:

- Відсутні або некоректні sensors
- Проблеми з командами (switches, numbers, selects)
- Помилки в логах Home Assistant

Створіть issue: <https://github.com/TarasKhust/ecoflow-api-mqtt/issues>

## 🔗 Посилання

- GitHub: <https://github.com/TarasKhust/ecoflow-api-mqtt>
- Branch: `feature/delta-pro-support`
- Issues: <https://github.com/TarasKhust/ecoflow-api-mqtt/issues>

---

**⚠️ BETA VERSION - FOR TESTING ONLY**

**Сумісність: Home Assistant 2024.x+**
