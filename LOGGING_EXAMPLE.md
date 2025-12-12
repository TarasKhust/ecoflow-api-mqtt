# 📊 Приклади логів - Детальне відстеження роботи

## Що тепер логується

### 1. **REST запити** (кожні N секунд з конфігу)

```
🔄 [14:23:15] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=15.1s, mqtt=ON)
🌐 [14:23:15] Fetching REST data for 0274...
✅ [14:23:15] REST update for 0274: received 160 fields, 3 changed
📊 [14:23:15] Changed fields (3 total):
   • bmsBattSoc: 85 → 84
   • invOutputWatts: 120 → 118
   • bpBattSoc: 85 → 84
🔀 [14:23:15] Merged data for 0274: REST=160 + MQTT=250 = Total=269 unique fields
```

**Що можна перевірити:**
- ✅ **Timestamp** - точний час запиту
- ✅ **configured_interval** - налаштований інтервал (15s)
- ✅ **actual_since_last** - реальний час між запитами (15.1s ≈ 15s) ✓
- ✅ **mqtt=ON/OFF** - стан MQTT
- ✅ **Кількість полів** - скільки прийшло (160)
- ✅ **Змінені поля** - які саме і як (з → на)
- ✅ **Об'єднання** - REST + MQTT = Total

---

### 2. **MQTT повідомлення** (в реальному часі)

```
⚡ [14:23:17] MQTT message for 0274: 5 fields updated
   Fields: invOutputWatts, invOutputVolt, invOutputAmp, invOutputFreq, invOutputTemp
   Total MQTT fields: 250 → 250 (no new fields)

⚡ [14:23:19] MQTT message for 0274: 3 fields updated
   Fields: bmsBattSoc, bpBattSoc, soc
   Total MQTT fields: 250 → 250 (no new fields)

⚡ [14:23:21] MQTT message for 0274: 8 fields updated
   Fields: invInputWatts, acInputWatts, solarInputWatts, bmsInputWatts ... (+4 more)
   Total MQTT fields: 250 → 253 (+3 new)
```

**Що можна перевірити:**
- ✅ **Частота** - MQTT приходить кожні 2-3 секунди
- ✅ **Кількість полів** - скільки оновилося в цьому повідомленні
- ✅ **Які поля** - конкретні назви (до 10 показується, решта "+N more")
- ✅ **Накопичення** - скільки всього MQTT полів зібралося

---

### 3. **Перше підключення MQTT**

```
Setting up MQTT for device MR51ZES5PG860274
MQTT connected successfully for device MR51ZES5PG860274
⚠️ Hybrid mode active: MQTT for real-time updates + REST every 15 seconds for all fields
```

**Що перевіряємо:**
- ✅ Інтервал **НЕ змінився** (було 15s, залишилося 15s)
- ✅ Немає повідомлення "interval changed"

---

### 4. **Стабільний стан** (немає змін)

```
🔄 [14:23:30] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=15.0s, mqtt=ON)
🌐 [14:23:30] Fetching REST data for 0274...
✅ [14:23:30] REST update for 0274: received 160 fields, 0 changed
📊 [14:23:30] No changes detected (device in stable state)
🔀 [14:23:30] Merged data for 0274: REST=160 + MQTT=253 = Total=271 unique fields
```

**Що бачимо:**
- ✅ **0 changed** - пристрій в стабільному стані
- ✅ **actual_since_last=15.0s** - інтервал точний! ✓

---

## Перевірка інтервалу опитування

### Як перевірити, що інтервал дійсно 15 секунд:

1. **Дивіться на `actual_since_last`** в логах:
```
[14:23:00] actual_since_last=0.0s     (перший запит)
[14:23:15] actual_since_last=15.1s    ✅ (15 секунд)
[14:23:30] actual_since_last=15.0s    ✅ (15 секунд)
[14:23:45] actual_since_last=15.2s    ✅ (15 секунд)
[14:24:00] actual_since_last=14.9s    ✅ (15 секунд)
```

2. **Рахуйте timestamps**:
```
14:23:00 → 14:23:15 = 15 секунд ✅
14:23:15 → 14:23:30 = 15 секунд ✅
14:23:30 → 14:23:45 = 15 секунд ✅
```

---

## Типові сценарії

### Сценарій 1: Активне використання (багато змін)

```
🔄 [14:25:00] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=15.0s, mqtt=ON)
✅ [14:25:00] REST update for 0274: received 160 fields, 12 changed
📊 [14:25:00] Changed fields (12 total):
   • invOutputWatts: 120 → 850
   • acOutputOn: 0 → 1
   • invOutputVolt: 230 → 232
   • invOutputAmp: 0.5 → 3.6
   ... (показує всі 12)
```

### Сценарій 2: Режим очікування (мало змін)

```
🔄 [14:25:15] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=15.1s, mqtt=ON)
✅ [14:25:15] REST update for 0274: received 160 fields, 1 changed
📊 [14:25:15] Changed fields (1 total):
   • bmsBattSoc: 84 → 83
```

### Сценарій 3: Тільки MQTT активний (між REST запитами)

```
⚡ [14:25:03] MQTT message for 0274: 2 fields updated
⚡ [14:25:06] MQTT message for 0274: 3 fields updated
⚡ [14:25:09] MQTT message for 0274: 2 fields updated
⚡ [14:25:12] MQTT message for 0274: 4 fields updated
🔄 [14:25:15] REST UPDATE TRIGGERED for 0274 ...
```

---

## Фільтрація логів в Home Assistant

### Показати тільки REST запити:
```
grep "REST UPDATE TRIGGERED" home-assistant.log
```

### Показати тільки MQTT повідомлення:
```
grep "MQTT message" home-assistant.log
```

### Показати тільки зміни:
```
grep "Changed fields" home-assistant.log
```

### Перевірити інтервал за останні 5 хвилин:
```
grep "REST UPDATE TRIGGERED" home-assistant.log | tail -20
```

---

## Що означають символи:

- 🔄 - REST запит почався
- 🌐 - Завантаження з API
- ✅ - Успішно отримано
- 📊 - Статистика змін
- 🔀 - Об'єднання REST + MQTT
- ⚡ - MQTT повідомлення
- 📡 - Тільки REST (без MQTT)
- ⚠️ - Важлива інформація

---

**Готово до тестування!** 🎯

Перезавантажте Home Assistant і дивіться логи в **Settings → System → Logs** або через файл `home-assistant.log`.

