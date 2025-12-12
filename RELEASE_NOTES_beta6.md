# 🚀 EcoFlow API v1.4.0-beta6

## 🐛 Hotfix: Logging for REST-only mode

### Problem Fixed
В v1.4.0-beta5 детальні логи працювали **тільки** в hybrid mode (REST + MQTT).
Користувачі без MQTT **НЕ бачили** логів.

### Solution
Додано те саме детальне логування в базовий `EcoFlowDataCoordinator` (REST-only mode).

## 📊 Тепер логи працюють в обох режимах:

### REST-only mode (без MQTT):
```log
🔄 [17:35:15] REST UPDATE for 0274 (interval=15s, mode=REST-only)
✅ [17:35:15] REST update for 0274: received 160 fields, 3 changed
📊 [17:35:15] Changed fields (3 total):
   • bmsBattSoc: 85 → 84
   • invOutputWatts: 120 → 118
   • bpBattSoc: 85 → 84
```

### Hybrid mode (REST + MQTT):
```log
🔄 [17:35:15] REST UPDATE TRIGGERED for 0274 (configured_interval=15s, actual_since_last=15.1s, mqtt=ON)
✅ [17:35:15] REST update for 0274: received 160 fields, 3 changed
📊 [17:35:15] Changed fields (3 total):
   • bmsBattSoc: 85 → 84
🔀 [17:35:15] Merged: REST=160 + MQTT=250 = Total=269 fields
⚡ [17:35:17] MQTT message: 5 fields updated
```

## 📥 Встановлення

### Через HACS:
1. HACS → Integrations → EcoFlow API
2. Update → v1.4.0-beta6
3. Restart Home Assistant

### Вручну:
1. Завантажте `ecoflow-api-v1.4.0-beta6.zip`
2. Розпакуйте в `custom_components/`
3. Restart Home Assistant

## ✅ Перевірка

Після встановлення:
1. Settings → System → Logs
2. Filter: `ecoflow_api`
3. Має з'явитися логування **незалежно** від наявності MQTT

## 📝 Changelog

### Fixed
- Додано детальне логування в REST-only coordinator
- Тепер логи працюють навіть без MQTT

### Changed  
- Відмінності в логах: "mode=REST-only" vs "mqtt=ON/OFF"

---

**Дякую @TarasKhust за звіт про проблему!** 🙏

Якщо знайдете інші проблеми - створіть [issue](https://github.com/TarasKhust/ecoflow-api-mqtt/issues)

