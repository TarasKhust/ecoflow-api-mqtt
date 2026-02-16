# Project Rules

## Overview

Home Assistant custom integration for EcoFlow devices via the official Developer API.
Supports Delta Pro 3, Delta Pro, Delta 2, Stream Ultra X, Smart Plug S401.

## Architecture

### Directory Structure

```
custom_components/ecoflow_api/
    # Core infrastructure (device-agnostic)
    __init__.py          # HA entry point, platform setup
    const.py             # DOMAIN, CONF_*, API URLs, defaults only
    api.py               # Generic REST API client (auth, get/set quota)
    coordinator.py       # REST-only DataUpdateCoordinator
    hybrid_coordinator.py # REST + MQTT coordinator
    mqtt_client.py       # MQTT client
    config_flow.py       # Config flow (device types from registry)
    entity.py            # EcoFlowBaseEntity base class

    # Command builders (Strategy pattern)
    commands/
        base.py          # CommandFormat enum + CommandBuilder protocol
        pro_v2.py        # Delta Pro 3, Stream Ultra X
        pro_v1.py        # Delta Pro (original)
        delta_v2.py      # Delta 2
        smart_plug.py    # Smart Plug S401

    # Device profiles (one folder per device)
    devices/
        __init__.py      # Registry: get_profile(), get_device_types()
        base.py          # Frozen dataclasses: EcoFlowSensorDef, EcoFlowSwitchDef, etc.
        delta_pro_3/     # __init__.py + sensors.py, switches.py, numbers.py, ...
        delta_pro/
        delta_2/
        stream_ultra_x/
        smart_plug/

    # Platforms (one generic class per platform)
    sensor.py
    switch.py
    number.py
    select.py
    binary_sensor.py
    button.py
```

### Key Design Patterns

- **Adding a new device** = create a new folder under `devices/` with a `PROFILE` object. No existing files need modification.
- **Strategy pattern** for commands: 4 formats (`PRO_V2`, `PRO_V1`, `DELTA_V2`, `SMART_PLUG`) behind `build_command()` factory.
- **Frozen dataclasses** for entity definitions (`EcoFlowSensorDef`, `EcoFlowSwitchDef`, etc.) in `devices/base.py`.
- **One class per platform**: e.g., a single `EcoFlowSwitch` handles all device types.
- **Device registry** in `devices/__init__.py` auto-wires profiles from subfolders.
- Each device folder's `__init__.py` exports a `PROFILE = DeviceProfile(...)` instance.

### Device Profile Structure

Each device folder contains:

- `__init__.py` - exports `PROFILE` with `device_type`, `display_name`, `command_format`, and entity lists
- `sensors.py` - `SENSORS: list[EcoFlowSensorDef]`
- `switches.py` - `SWITCHES: list[EcoFlowSwitchDef]`
- `numbers.py` - `NUMBERS: list[EcoFlowNumberDef]`
- `selects.py` - `SELECTS: list[EcoFlowSelectDef]`
- `binary_sensors.py` - `BINARY_SENSORS: list[EcoFlowBinarySensorDef]`
- `buttons.py` - `BUTTONS: list[EcoFlowButtonDef]` (optional)

### Command Formats

| Format       | Devices                     | Key params                             |
| ------------ | --------------------------- | -------------------------------------- |
| `PRO_V2`     | Delta Pro 3, Stream Ultra X | `cmdId`, `cmdFunc` (defaults: 17, 254) |
| `PRO_V1`     | Delta Pro                   | `cmd_set`, `cmd_id`                    |
| `DELTA_V2`   | Delta 2                     | `module_type`, `operate_type`          |
| `SMART_PLUG` | Smart Plug S401             | `cmd_code`                             |

### State Interpreters (switches)

- `"bool"` - default, standard bool/int coercion
- `"int01"` - integer 0=off, 1=on
- `"flow_info"` - integer 0=off, 2=on (Delta Pro 3 flowInfo keys)

## Coding Rules

### Type Safety

- Do not use `typing.Any` in the codebase. Use proper types: `TypedDict`, `object`, union types, `Protocol`, or specific types instead.

### Style

- Use `from __future__ import annotations` in every Python file.
- Use frozen dataclasses for entity definitions (immutable configuration).
- Entity keys (`key` field in dataclasses) must be stable - changing them breaks user automations.
- Prefer `dict[str, ...]` over `Dict[str, ...]` (modern Python type syntax).
- Use `str | None` over `Optional[str]`.
- Platform files should stay thin - entity definitions belong in `devices/<device>/`.
- No device-specific logic in `const.py`, `api.py`, or `coordinator.py`.

### Naming Conventions

- Entity keys: `snake_case` (e.g., `ac_hv_out`, `bms_batt_soc`)
- State keys: match API response keys exactly (e.g., `flowInfoAcHvOut`, `bmsBattSoc`)
- Param keys: match API command parameter names (e.g., `cfgHvAcOutOpen`, `cfgBeepEn`)
- Device module lists: `SENSORS`, `SWITCHES`, `NUMBERS`, `SELECTS`, `BINARY_SENSORS`, `BUTTONS`
- Device profile export: `PROFILE`

### Entity Unique IDs

Format: `{device_sn}_{entity_key}` - scoped per HA platform.
Cross-platform key overlap is allowed (e.g., sensor + number both using `ac_standby_time`).
Within-platform keys must be unique per device.
