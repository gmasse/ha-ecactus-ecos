"""eCactus ECOS integration."""

from dataclasses import dataclass
import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .coordinator import EcosConfigEntry, EcosDataCoordinator

CONF_DATACENTER = "datacenter"

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: EcosConfigEntry) -> bool:
    """Set up ECOS client from a config entry."""

    coordinator = EcosDataCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True
