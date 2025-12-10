# Delta Pro 3 API Mapping

Цей документ містить повний опис даних, які повертає API для Delta Pro 3, на основі реального тестування пристрою.

## Тестовий пристрій
- **Модель**: DELTA Pro 3
- **Serial Number**: MR51ZES5PG860274
- **Статус**: Online
- **Дата тестування**: 2025-12-10

---

## 📊 Основні сенсори

### Батарея (BMS - Battery Management System)

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `bmsBattSoc` | Battery Level (BMS) | % | 42.99 | Рівень заряду батареї |
| `bmsBattSoh` | State of Health (BMS) | % | 100.0 | Стан здоров'я батареї |
| `bmsChgRemTime` | Charge Remaining Time | min | 183 | Час до повного заряду |
| `bmsDsgRemTime` | Discharge Remaining Time | min | 5939 | Час до повного розряду |
| `bmsDesignCap` | Design Capacity | mAh | 80000 | Проектна ємність (80 Ah) |
| `bmsChgDsgState` | Charge/Discharge State | - | 2 | Стан: 0=idle, 1=charge, 2=discharge |

### Батарея (CMS - Central Management System)

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `cmsBattSoc` | Battery Level (CMS) | % | 44.34 | Рівень заряду (CMS) |
| `cmsBattSoh` | State of Health (CMS) | % | 100.0 | Стан здоров'я (CMS) |
| `cmsChgRemTime` | Charge Remaining Time | min | 183 | Час заряду |
| `cmsDsgRemTime` | Discharge Remaining Time | min | 5939 | Час розряду |
| `cmsBattFullEnergy` | Full Energy Capacity | Wh | 8192 | Повна енергоємність |
| `cmsMaxChgSoc` | Max Charge Level | % | 100 | Максимальний рівень заряду |
| `cmsMinDsgSoc` | Min Discharge Level | % | 0 | Мінімальний рівень розряду |
| `cmsBattPowInMax` | Max Input Power | W | 1697 | Макс. вхідна потужність |
| `cmsBattPowOutMax` | Max Output Power | W | 4000 | Макс. вихідна потужність |

---

## ⚡ Потужність

### Загальна потужність

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `powInSumW` | Total Input Power | W | 1701.0 | Загальна вхідна потужність |
| `powOutSumW` | Total Output Power | W | 0.0 | Загальна вихідна потужність |

### AC (змінний струм)

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `powGetAcIn` | AC Input Power | W | 1701.0 | Вхідна потужність AC |
| `powGetAc` | AC Output Power | W | 0.0 | Вихідна потужність AC |
| `powGetAcHvOut` | AC HV Output Power | W | 0.0 | AC High Voltage вихід |
| `powGetAcLvOut` | AC LV Output Power | W | 0.0 | AC Low Voltage вихід |
| `acOutFreq` | AC Output Frequency | Hz | 50 | Частота AC виходу |
| `plugInInfoAcInChgPowMax` | AC Max Charge Power | W | 1697 | Макс. потужність AC заряду |
| `plugInInfoAcInChgHalPowMax` | AC Half Max Power | W | 2900 | Половина макс. потужності |
| `plugInInfoAcOutDsgPowMax` | AC Max Discharge Power | W | 4000 | Макс. вихідна потужність AC |

### Solar (сонячні панелі)

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `powGetPvH` | Solar Input Power (High) | W | 0.0 | Сонячний вхід (високовольтний) |
| `powGetPvL` | Solar Input Power (Low) | W | 0.0 | Сонячний вхід (низьковольтний) |

### DC виходи

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `powGet12v` | 12V DC Output Power | W | 0.0 | Вихід 12V DC |
| `powGet24v` | 24V DC Output Power | W | 0.0 | Вихід 24V DC |
| `powGetTypec1` | USB-C1 Output Power | W | 0.0 | USB-C порт 1 |
| `powGetTypec2` | USB-C2 Output Power | W | 0.0 | USB-C порт 2 |
| `powGetQcusb1` | QC USB1 Output Power | W | 0.0 | Quick Charge USB 1 |
| `powGetQcusb2` | QC USB2 Output Power | W | 0.0 | Quick Charge USB 2 |

---

## 🌡️ Температура

| API Key | Назва | Одиниці | Приклад значення | Опис |
|---------|-------|---------|------------------|------|
| `bmsMaxCellTemp` | Max Cell Temperature | °C | 29 | Макс. температура комірки |
| `bmsMinCellTemp` | Min Cell Temperature | °C | 26 | Мін. температура комірки |
| `bmsMaxMosTemp` | Max MOSFET Temperature | °C | 29 | Макс. температура MOSFET |
| `bmsMinMosTemp` | Min MOSFET Temperature | °C | 27 | Мін. температура MOSFET |

---

## 🔌 Статуси підключення (Binary Sensors)

| API Key | Назва | Тип | Приклад | Опис |
|---------|-------|-----|---------|------|
| `plugInInfoAcChargerFlag` | AC Charging | bool | true | Заряджається від AC |
| `plugInInfoPvHChargerFlag` | Solar Charging (High) | bool | false | Заряджається від сонця (HV) |
| `plugInInfoPvLChargerFlag` | Solar Charging (Low) | bool | false | Заряджається від сонця (LV) |
| `plugInInfo4p81ChargerFlag` | 4P81 Charging | bool | false | Заряджається через 4P81 |
| `plugInInfo4p82ChargerFlag` | 4P82 Charging | bool | false | Заряджається через 4P82 |
| `plugInInfo5p8ChargerFlag` | 5P8 Charging | bool | false | Заряджається через 5P8 |
| `plugInInfoAcInFlag` | AC Input Connected | int | 0 | AC вхід підключено |
| `plugInInfoPvHFlag` | Solar HV Connected | int | 0 | Сонце HV підключено |
| `plugInInfoPvLFlag` | Solar LV Connected | int | 0 | Сонце LV підключено |

---

## ⚙️ Налаштування

### Таймери

| API Key | Назва | Одиниці | Приклад | Опис |
|---------|-------|---------|---------|------|
| `acStandbyTime` | AC Standby Time | min | 0 | Час до вимкнення AC (0=ніколи) |
| `dcStandbyTime` | DC Standby Time | min | 0 | Час до вимкнення DC (0=ніколи) |
| `screenOffTime` | Screen Off Time | s | 300 | Час до вимкнення екрану |
| `bleStandbyTime` | BLE Standby Time | s | 3600 | Час до вимкнення Bluetooth |
| `devStandbyTime` | Device Standby Time | min | 0 | Загальний час очікування |

### Дисплей

| API Key | Назва | Одиниці | Приклад | Опис |
|---------|-------|---------|---------|------|
| `lcdLight` | LCD Brightness | % | 100 | Яскравість екрану |

### Функції

| API Key | Назва | Тип | Приклад | Опис |
|---------|-------|-----|---------|------|
| `xboostEn` | X-Boost Enabled | bool | true | X-Boost увімкнено |
| `enBeep` | Beep Enabled | bool | false | Звуковий сигнал увімкнено |
| `acEnergySavingOpen` | AC Energy Saving | bool | false | Енергозбереження AC |
| `fastChargeSwitch` | Fast Charge | int | 1 | Швидкий заряд |
| `outputPowerOffMemory` | Power Off Memory | bool | true | Пам'ять стану виходів |

### Backup та захист

| API Key | Назва | Одиниці | Приклад | Опис |
|---------|-------|---------|---------|------|
| `energyBackupEn` | Energy Backup | bool | false | Резервне живлення |
| `energyBackupStartSoc` | Backup Start SOC | % | 50 | Рівень старту backup |
| `backupReverseSoc` | Backup Reverse SOC | % | 50 | Зворотний рівень backup |
| `llcGFCIFlag` | GFCI Triggered | bool | false | Спрацювання захисту GFCI |

### Storm Pattern (режим шторму)

| API Key | Назва | Тип | Приклад | Опис |
|---------|-------|-----|---------|------|
| `stormPatternEnable` | Storm Pattern | bool | true | Режим шторму увімкнено |
| `stormPatternOpenFlag` | Storm Pattern Active | bool | false | Режим шторму активний |
| `stormPatternEndTime` | Storm End Time | timestamp | 0 | Час закінчення режиму |

### Generator (генератор)

| API Key | Назва | Тип | Приклад | Опис |
|---------|-------|-----|---------|------|
| `generatorCareModeOpen` | Generator Care Mode | bool | false | Режим догляду за генератором |
| `generatorCareModeStartTime` | Generator Start Time | min | 1080 | Час старту генератора |
| `generatorPvHybridModeOpen` | PV Hybrid Mode | bool | false | Гібридний режим PV |
| `generatorPvHybridModeSocMax` | PV Hybrid Max SOC | % | 100 | Макс. SOC для гібриду |

---

## 🔄 Стани потоку

| API Key | Назва | Значення | Опис |
|---------|-------|----------|------|
| `flowInfoAcIn` | AC Input Flow | 2 | Стан AC входу |
| `flowInfoAcHvOut` | AC HV Output Flow | 2 | Стан AC HV виходу |
| `flowInfoAcLvOut` | AC LV Output Flow | 0 | Стан AC LV виходу |
| `flowInfo12v` | 12V Flow | 2 | Стан 12V виходу |
| `flowInfo24v` | 24V Flow | 2 | Стан 24V виходу |
| `flowInfoTypec1` | USB-C1 Flow | 14 | Стан USB-C1 |
| `flowInfoTypec2` | USB-C2 Flow | 14 | Стан USB-C2 |
| `flowInfoQcusb1` | QC USB1 Flow | 14 | Стан QC USB1 |
| `flowInfoQcusb2` | QC USB2 Flow | 14 | Стан QC USB2 |
| `flowInfoPvH` | Solar HV Flow | 0 | Стан сонячного HV |
| `flowInfoPvL` | Solar LV Flow | 0 | Стан сонячного LV |

---

## 🔧 Технічна інформація

### Підключені пристрої

| API Key | Значення | Опис |
|---------|----------|------|
| `plugInInfoDcp2Sn` | MR52Z1S5PG8R0374 | Serial number підключеного DCP2 |
| `plugInInfoDcpSn` | "" | Serial number DCP |
| `plugInInfo5p8Sn` | "" | Serial number 5P8 |

### Часова зона

| API Key | Значення | Опис |
|---------|----------|------|
| `utcTimezone` | 200 | Зміщення UTC (200 = UTC+2) |
| `utcTimezoneId` | "Europe/Kiev" | ID часової зони |
| `utcSetMode` | false | Режим налаштування UTC |

### Коди помилок

| API Key | Значення | Опис |
|---------|----------|------|
| `errcode` | 0 | Код помилки API (0 = OK) |
| `bmsErrCode` | 0 | Код помилки BMS (0 = OK) |
| `mpptErrCode` | 0 | Код помилки MPPT (0 = OK) |

---

## ❌ Відсутні дані в REST API

### Cycles (кількість циклів)

**Важливо**: Delta Pro 3 **REST API НЕ повертає** інформацію про кількість циклів заряду/розряду (`cycles`).

#### Чому немає cycles?

**Cycles доступні тільки через MQTT (WebSocket), а не через REST API!**

- **REST API** (`/iot-open/sign/device/quota/all`) - офіційний Developer API, не включає cycles
- **MQTT/WebSocket** - EcoFlow Cloud протокол, включає cycles та більше даних в real-time

#### Порівняння підходів:

| Параметр | REST API (наш) | MQTT (tolwi) |
|----------|----------------|--------------|
| Cycles | ❌ Немає | ✅ Є |
| Офіційна підтримка | ✅ Так | ❌ Ні |
| Стабільність | ✅ Висока | ⚠️ Середня |
| Оновлення | 15-60 сек | 1-5 сек |
| Складність | ✅ Проста | ⚠️ Складна |

#### Альтернативи:

**1. Розрахунок на основі SOH (State of Health)**

Формула: `Estimated Cycles ≈ (100 - SOH) × 10`

Для вашої батареї:
- SOH = 100% → Cycles ≈ 0 (нова батарея)
- SOH = 90% → Cycles ≈ 100
- SOH = 80% → Cycles ≈ 200

**2. Відстеження через Home Assistant**

Можна створити template sensor:

```yaml
template:
  - sensor:
      - name: "Delta Pro 3 Estimated Cycles"
        unique_id: delta_pro_3_estimated_cycles
        state: >
          {% set soh = states('sensor.delta_pro_3_state_of_health_bms') | float(100) %}
          {{ ((100 - soh) * 10) | round(0) }}
        unit_of_measurement: "cycles"
        icon: mdi:battery-heart-variant
```

**3. Використання обох інтеграцій**

- Наша інтеграція (REST API) - для стабільного моніторингу
- [tolwi/hassio-ecoflow-cloud](https://github.com/tolwi/hassio-ecoflow-cloud) (MQTT) - для cycles та real-time даних

---

## 📝 Команди управління

Доступні команди для Delta Pro 3 (префікс `WN511_`):

| Команда | Опис | Параметри |
|---------|------|-----------|
| `WN511_SET_AC_CHARGE_SPEED` | Встановити потужність AC заряду | `acChgPower` (200-3000W), `chgPauseFlag` |
| `WN511_SET_CHARGE_LEVEL` | Встановити рівні заряду/розряду | `maxChgSoc` (50-100%), `minDsgSoc` (0-30%) |
| `WN511_SET_AC_OUT` | Увімкнути/вимкнути AC вихід | `acOutState` (0/1) |
| `WN511_SET_DC_OUT` | Увімкнути/вимкнути DC вихід | `dcOutState` (0/1) |
| `WN511_SET_12V_DC_OUT` | Увімкнути/вимкнути 12V DC | `dc12vOutState` (0/1) |
| `WN511_SET_24V_DC_OUT` | Увімкнути/вимкнути 24V DC | `dc24vOutState` (0/1) |
| `WN511_SET_USB_OUT` | Увімкнути/вимкнути USB | `usbOutState` (0/1) |
| `WN511_SET_AC_STANDBY_TIME` | Час очікування AC | `acStandbyTime` (хвилини) |
| `WN511_SET_DC_STANDBY_TIME` | Час очікування DC | `dcStandbyTime` (хвилини) |
| `WN511_SET_LCD_STANDBY_TIME` | Час очікування екрану | `lcdOffTime` (секунди) |
| `WN511_SET_BEEP` | Увімкнути/вимкнути звук | `beepState` (0/1) |
| `WN511_SET_X_BOOST` | Увімкнути/вимкнути X-Boost | `xBoostState` (0/1) |

---

## 📚 Джерела

- **Офіційна документація**: https://developer-eu.ecoflow.com/us/document/deltaPro3
- **API Base URL**: https://api-e.ecoflow.com
- **Тестовий файл**: `api_response_MR51ZES5PG860274.json`
- **Дата тестування**: 2025-12-10

---

## 🎯 Використання в Home Assistant

Всі ці дані тепер доступні через константи:
- `DELTA_PRO_3_SENSORS` - сенсори (читання)
- `DELTA_PRO_3_BINARY_SENSORS` - бінарні сенсори (стани)
- `DELTA_PRO_3_SWITCHES` - перемикачі (управління)
- `DELTA_PRO_3_NUMBERS` - числові значення (налаштування)

Файл: `custom_components/ecoflow_api/const.py`

