"""Base entity for EcoFlow API integration."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EcoFlowDataCoordinator
from .devices import get_profile


class EcoFlowBaseEntity(CoordinatorEntity[EcoFlowDataCoordinator]):
    """Base class for EcoFlow entities.

    This base class provides:
    - Common device info
    - Unique ID generation
    - Coordinator integration
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoFlowDataCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Data update coordinator
            entity_key: Unique key for this entity type
        """
        super().__init__(coordinator)
        self._entity_key = entity_key
        self._attr_unique_id = f"{coordinator.device_sn}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        # Get firmware and hardware versions from data if available
        sw_version = None
        hw_version = None

        if self.coordinator.data:
            # Try different possible keys for firmware version
            sw_version = (
                self.coordinator.data.get("sysVer")
                or self.coordinator.data.get("sysVersion")
                or self.coordinator.data.get("firmwareVersion")
            )
            # Try different possible keys for hardware version
            hw_version = (
                self.coordinator.data.get("hwVer")
                or self.coordinator.data.get("hwVersion")
                or self.coordinator.data.get("hardwareVersion")
            )

            # Convert sysVer to string if it's a number
            if sw_version and isinstance(sw_version, (int, float)):
                sw_version = str(sw_version)

        profile = get_profile(self.coordinator.device_type)
        display_name = profile.display_name if profile else self.coordinator.device_type

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_sn)},
            name=f"EcoFlow {display_name}",
            manufacturer="EcoFlow",
            model=display_name,
            serial_number=self.coordinator.device_sn,
            sw_version=sw_version,
            hw_version=hw_version,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    def with_category(self, category: EntityCategory) -> EcoFlowBaseEntity:
        """Set entity category (builder pattern).

        Args:
            category: Entity category to set

        Returns:
            Self for method chaining
        """
        self._attr_entity_category = category
        return self

    def with_device_class(self, device_class: str) -> EcoFlowBaseEntity:
        """Set device class (builder pattern).

        Args:
            device_class: Device class to set

        Returns:
            Self for method chaining
        """
        self._attr_device_class = device_class
        return self

    def with_icon(self, icon: str) -> EcoFlowBaseEntity:
        """Set icon (builder pattern).

        Args:
            icon: Icon to set

        Returns:
            Self for method chaining
        """
        self._attr_icon = icon
        return self

    def with_state_class(self, state_class: str) -> EcoFlowBaseEntity:
        """Set state class (builder pattern).

        Args:
            state_class: State class to set

        Returns:
            Self for method chaining
        """
        self._attr_state_class = state_class
        return self
