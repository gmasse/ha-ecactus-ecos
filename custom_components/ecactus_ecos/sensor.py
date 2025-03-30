"""Sensor."""

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import EcosConfigEntry, EcosDataCoordinator, DeviceData
from .entity import EcosInverterEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EcosInverterSensorDescription(SensorEntityDescription):
    """Describe an ECOS sensor."""

    value_fn: Callable[[DeviceData | None], int | float | None]


ECOS_INVERTER_SENSOR_TYPES: tuple[EcosInverterSensorDescription, ...] = (
    # Power Sensors
    EcosInverterSensorDescription(
        key="home",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=(lambda data: None if data is None else data.metrics.home),
    ),
    EcosInverterSensorDescription(
        key="solar",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=(lambda data: None if data is None else data.metrics.solar),
    ),
    EcosInverterSensorDescription(
        key="meter",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=(lambda data: None if data is None else data.metrics.meter),
    ),
    EcosInverterSensorDescription(
        key="grid",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=(lambda data: None if data is None else data.metrics.grid),
    ),
    # Energy Sensors
    EcosInverterSensorDescription(
        key="consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.consumption),
    ),
    EcosInverterSensorDescription(
        key="from_battery",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.from_battery),
    ),
    EcosInverterSensorDescription(
        key="to_battery",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.to_battery),
    ),
    EcosInverterSensorDescription(
        key="from_grid",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.from_grid),
    ),
    EcosInverterSensorDescription(
        key="to_grid",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.to_grid),
    ),
    EcosInverterSensorDescription(
        key="from_solar",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.from_solar),
    ),
    EcosInverterSensorDescription(
        key="eps",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=(lambda data: None if data is None else data.energy.eps),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EcosConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the ECOS sensors based on a config entry."""
    _LOGGER.debug("Setting sensors")
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: EcosDataCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = [
        EcosInverterSensor(coordinator, sensor, device_id)
        for device_id in coordinator.data
        for sensor in ECOS_INVERTER_SENSOR_TYPES
    ]

    async_add_entities(entities)


class EcosInverterSensor(EcosInverterEntity, SensorEntity):
    """Represents a ECOS sensor."""

    entity_description: EcosInverterSensorDescription

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data(self.device_id))
