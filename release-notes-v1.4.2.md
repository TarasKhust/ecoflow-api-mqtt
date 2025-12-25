# 🎉 Stable Release v1.4.2 - Energy Strategy and Generator Controls

**Велике оновлення з повною підтримкою керування енергетичними режимами для EcoFlow DeltaPro3!**

## ✨ Нові функції:

### 📊 Backup Reserve Control

- **number.backup_reserve_level** - Slider для налаштування рівня резервного живлення (0-100%)
- Використовує nested API структуру `cfgEnergyBackup`

### ⚡ Energy Strategy Mode

- **select.energy_strategy_mode** - Вибір режиму роботи:
  - Off (вимкнено)
  - Self-Powered (самостійне забезпечення)
  - TOU (Time of Use)
- Підтримка nested API параметрів `cfgEnergyStrategyOperateMode`

### 🔧 Generator Controls

- **switch.generator_pv_hybrid_mode** - Гібридний режим генератора з PV
- **switch.generator_care_mode** - Режим догляду за генератором
- **number.generator_pv_hybrid_max_soc** - Максимальний SOC для гібридного режиму (0-100%)
- **number.generator_care_start_time** - Час початку режиму догляду (0-1440 хв)

## 🔧 Вдосконалення:

- ✅ Правильні імена всіх entities (вирішено проблему з "None")
- ✅ Унікальні ID для всіх entities
- ✅ Сумісні іконки для Home Assistant
- ✅ Nested параметри для складних API команд
- ✅ Збереження станів при перемиканні режимів

## 📦 Встановлення:

### Через HACS:

1. HACS → Integrations → EcoFlow API
2. Download (остання версія)
3. Restart Home Assistant

### Або вручну:

1. Завантажити ZIP з [Releases](https://github.com/TarasKhust/ecoflow-api-mqtt/releases/tag/v1.4.2)
2. Розпакувати в `custom_components/ecoflow_api/`
3. Restart Home Assistant

## 🧪 Тестування:

### Backup Reserve:

1. Знайдіть `number.ecoflow_delta_pro_3_backup_reserve_level`
2. Встановіть значення через slider
3. Перевірте, що зберігається

### Energy Strategy:

1. Знайдіть `select.ecoflow_delta_pro_3_energy_strategy_mode`
2. Перемкніть між режимами
3. Перевірте реакцію пристрою

### Generator:

1. Перевірте generator switches та numbers
2. Протестуйте всі режими

## 🐛 Вирішені проблеми:

- Entity names showing as "None"
- Type errors in select.py
- Unsupported outline icons
- Unique ID conflicts
- Nested parameter handling

## 📝 API Команди:

### Backup Reserve:

```json
{
  "sn": "DEVICE_SN",
  "cmdId": 17,
  "params": {
    "cfgEnergyBackup": {
      "energyBackupEn": true,
      "energyBackupStartSoc": 50
    }
  }
}
```

### Energy Strategy:

```json
{
  "sn": "DEVICE_SN",
  "cmdId": 17,
  "params": {
    "cfgEnergyStrategyOperateMode": {
      "operateSelfPoweredOpen": true,
      "operateTouModeOpen": false,
      "operateScheduledOpen": false,
      "operateIntelligentScheduleModeOpen": false
    }
  }
}
```

## 🔗 Посилання:

- GitHub: https://github.com/TarasKhust/ecoflow-api-mqtt
- Issues: https://github.com/TarasKhust/ecoflow-api-mqtt/issues
- Документація: https://github.com/TarasKhust/ecoflow-api-mqtt

## 🙏 Подяка:

- **Linear Task**: https://linear.app/moneymanagerapp/issue/MON-13
- **GitHub Issue**: #1

**Велике дякую за тестування та підтримку! 🚀**

---

**ПОВНА СУМІСНІСТЬ З HOME ASSISTANT 2024.X+**
