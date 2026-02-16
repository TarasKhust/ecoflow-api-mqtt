"""Base classes for device profiles and entity definitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.helpers.entity import EntityCategory

from ..commands.base import CommandFormat

# =============================================================================
# Sensor
# =============================================================================


@dataclass(frozen=True)
class EcoFlowSensorDef:
    """Definition for a sensor entity."""

    key: str  # Unique entity key (e.g., "bms_batt_soc")
    name: str  # Display name
    state_key: str  # Key in coordinator.data (e.g., "bmsBattSoc")
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    icon: str | None = None
    entity_category: EntityCategory | None = None
    # For ENUM sensors
    options: list[str] | None = None
    # For extra battery array sensors
    resv_index: int | None = None
    resv_type: str | None = None  # "float", "mah_to_ah", etc.


# =============================================================================
# Binary Sensor
# =============================================================================


@dataclass(frozen=True)
class EcoFlowBinarySensorDef:
    """Definition for a binary sensor entity."""

    key: str
    name: str
    state_key: str  # Key in coordinator.data
    device_class: BinarySensorDeviceClass | None = None
    icon_on: str | None = None
    icon_off: str | None = None
    # Derived sensors: value computed from another sensor
    derived: bool = False
    derive_from: str | None = None
    derive_condition: Callable[[int | float | None], bool] | None = None


# =============================================================================
# Switch
# =============================================================================


@dataclass(frozen=True)
class EcoFlowSwitchDef:
    """Definition for a switch entity.

    The `command_params` dict holds format-specific kwargs for build_command():
      - ProV2 (Delta Pro 3): {} (no extra kwargs needed)
      - ProV1 (Delta Pro):   {"cmd_set": 32, "cmd_id": 66}
      - DeltaV2 (Delta 2):   {"module_type": 5, "operate_type": "acOutCfg"}
      - SmartPlug:            {"cmd_code": "WN511_..."}
    """

    key: str
    name: str
    state_key: str  # Key in coordinator.data to read current state
    param_key: str  # Key inside params dict for the command
    command_params: dict[str, int | str] = field(default_factory=dict)
    value_on: int | bool = True
    value_off: int | bool = False
    icon_on: str | None = None
    icon_off: str | None = None
    device_class: SwitchDeviceClass | None = None
    inverted: bool = False
    # How to interpret state value: "bool", "int01", "flow_info"
    state_interpreter: str = "bool"


# =============================================================================
# Number
# =============================================================================


@dataclass(frozen=True)
class EcoFlowNumberDef:
    """Definition for a number entity."""

    key: str
    name: str
    state_key: str
    param_key: str  # Key inside params dict
    command_params: dict[str, int | str] = field(default_factory=dict)
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    unit: str | None = None
    icon: str | None = None
    mode: NumberMode = NumberMode.SLIDER
    # For nested parameter structures (e.g., backup reserve level)
    nested_params: dict[str, int | float | str | None] | None = None
    # Value mapping functions (e.g., Smart Plug brightness 0-1023 <-> 0-100%)
    value_to_ui: Callable[[float], float] | None = None
    value_from_ui: Callable[[float], float] | None = None


# =============================================================================
# Select
# =============================================================================


@dataclass(frozen=True)
class EcoFlowSelectDef:
    """Definition for a select entity."""

    key: str
    name: str
    param_key: str  # Key inside params dict
    options: dict[str, int | str | dict[str, bool]]  # Display name -> API value mapping
    state_key: str | None = None  # None for local-only settings
    command_params: dict[str, int | str] = field(default_factory=dict)
    icon: str | None = None
    is_local: bool = False
    nested_params: bool = False


# =============================================================================
# Button
# =============================================================================


@dataclass(frozen=True)
class EcoFlowButtonDef:
    """Definition for a button entity."""

    key: str
    name: str
    param_key: str  # Key inside params dict
    command_params: dict[str, int | str] = field(default_factory=dict)
    param_value: int | str = 1
    icon: str | None = None


# =============================================================================
# Device Profile
# =============================================================================


@dataclass
class DeviceProfile:
    """Complete profile for a device type.

    Each device module creates one PROFILE instance that declares everything
    about the device: type, display name, command format, and all entity defs.
    Adding a new device = creating a new folder with a PROFILE.
    """

    device_type: str  # Internal key (e.g., "delta_pro_3")
    display_name: str  # Human-readable (e.g., "Delta Pro 3")
    command_format: CommandFormat  # Which command builder to use

    sensors: list[EcoFlowSensorDef] = field(default_factory=list)
    binary_sensors: list[EcoFlowBinarySensorDef] = field(default_factory=list)
    switches: list[EcoFlowSwitchDef] = field(default_factory=list)
    numbers: list[EcoFlowNumberDef] = field(default_factory=list)
    selects: list[EcoFlowSelectDef] = field(default_factory=list)
    buttons: list[EcoFlowButtonDef] = field(default_factory=list)
