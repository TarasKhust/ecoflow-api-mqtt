"""Base entity for EcoFlow API integration."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_TYPES
from .coordinator import EcoFlowDataCoordinator


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
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_sn)},
            name=f"EcoFlow {DEVICE_TYPES.get(self.coordinator.device_type, self.coordinator.device_type)}",
            manufacturer="EcoFlow",
            model=DEVICE_TYPES.get(
                self.coordinator.device_type,
                self.coordinator.device_type
            ),
            serial_number=self.coordinator.device_sn,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None


