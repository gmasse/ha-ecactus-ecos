"""Base entity for the ECOS integration."""

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EcosDataCoordinator


class EcosBaseEntity(CoordinatorEntity[EcosDataCoordinator]):
    """ECOS base entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcosDataCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the base Ecos sensor."""
        super().__init__(coordinator)

        self.entity_description = description


class EcosInverterEntity(EcosBaseEntity):
    """Defines an ECOS inverter entity."""

    def __init__(
        self,
        coordinator: EcosDataCoordinator,
        description: SensorEntityDescription,
        device_id: str,
    ) -> None:
        """Initialize the EcosInverter sensor entity."""
        super().__init__(coordinator, description)
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = description.key
        self._attr_device_info = DeviceInfo(
            manufacturer="eCactus",
            model=coordinator.data[device_id].device.device_type,
            name=self.coordinator.data[device_id].device.alias,
            identifiers={(DOMAIN, device_id)},
            serial_number=coordinator.data[device_id].device.serial,
        )
        self.device_id = device_id
