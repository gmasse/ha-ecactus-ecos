"""ECOS client data coordinator."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

import ecactus
import ecactus.model

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, IntegrationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DATACENTER, CONF_HOME_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

type EcosConfigEntry = ConfigEntry[EcosDataCoordinator]


@dataclass
class DeviceData:
    """Helper class to hold device-specific data."""

    device: ecactus.model.Device
    metrics: ecactus.model.PowerMetrics
    energy: ecactus.model.EnergyStatistics


@dataclass
class EcosData:
    """Class to hold information of all the ECOS devices.

    This is data that needs to be polled and updated at a relatively high
    frequency in order for this integration to function correctly.
    All this data is updated at the same time by a single coordinator.

    Allows direct access to device information using device_id:
    e.g. `ecos_data(device_id).metrics`

    Devices can be added using dictionary-like syntax:
    e.g. `ecos_data[device_id] = (device, metrics)`
    """

    def __init__(self) -> None:
        """Initialize an empty EcosData instance."""
        self._devices: dict[str, DeviceData] = {}
        # field(
        #    repr=False, hash=False, compare=False
        # )

    def __iter__(self) -> Iterator[str]:
        """Iterate over all device_ids in the EcosData instance."""
        yield from self._devices.keys()

    def __len__(self) -> int:
        """Return the number of devices."""
        return len(self._devices)

    def __call__(self, device_id: str) -> DeviceData | None:
        """Return DeviceData for a specific device_id.

        Args:
            device_id: The ID of the device to get information for.

        Returns:
            DeviceData: Contains the device info and metrics for the specified device_id.

        """
        return self._devices.get(device_id)

    def __setitem__(
        self,
        device_id: str,
        value: tuple[
            ecactus.model.Device,
            ecactus.model.PowerMetrics,
            ecactus.model.EnergyStatistics,
        ],
    ):
        """Add or update a device in the EcosData instance.

        Args:
            device_id: The ID of the device to add or update.
            value: A tuple containing the device and metrics objects.
                  Expected format: (ecactus.model.Device, ecactus.model.PowerMetrics, ecactus.model.EnergyStatistics)

        """
        device, metrics, energy = value
        self._devices[device_id] = DeviceData(
            device=device, metrics=metrics, energy=energy
        )

    def __getitem__(self, device_id: str) -> DeviceData:
        """Return DeviceData for a specific device_id.

        Args:
            device_id: The ID of the device to get information for.

        Returns:
            DeviceData: Contains the device and metrics for the specified device_id.

        """
        return self._devices[device_id]


class EcosDataCoordinator(DataUpdateCoordinator[EcosData]):
    """Data coordinator class."""

    config_entry: EcosConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: EcosConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.datacenter = config_entry.data[CONF_DATACENTER]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]
        self.home_id = config_entry.data[CONF_HOME_ID]

        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call to set up the coordinator
            setup_method=self.async_setup,
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )

        self.unique_id = config_entry.entry_id
        self._devices: list[ecactus.model.Device] = []

        # Initialize client
        self.session = ecactus.AsyncEcos(datacenter=self.datacenter)

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            _LOGGER.debug("Logging into ECOS")
            await self.session.login(self.username, self.password)
        # TODO: refining exception
        except Exception as err:
            raise ConfigEntryAuthFailed(f"Unable to logging: {err}") from err
        try:
            _LOGGER.debug("Fetching device list for home %s", self.home_id)
            device_list = await self.session.get_devices(self.home_id)
            for device in device_list:
                if device.type_int == 1:  # Inverter are the only supported devices
                    _LOGGER.debug("Adding device id %s", device.id)
                    self._devices.append(device)
        # TODO: refining exception
        except Exception as err:
            raise IntegrationError(f"Error retrieving devices: {err}") from err
        _LOGGER.debug("Data coordinator initialized")

    async def async_update_data(self) -> EcosData:
        """Fetch data from ECOS API."""
        data = EcosData()
        try:
            for device in self._devices:
                data[device.id] = (
                    device,
                    await self.session.get_realtime_device_data(device.id),
                    (
                        await self.session.get_insight(
                            device.id, period_type=0, start_date=datetime.now()
                        )
                    ).energy_statistics,
                )
                _LOGGER.debug(
                    "Saved data for device %s: %s", device.id, data[device.id]
                )
        # TODO: refining exception
        except Exception as err:
            raise UpdateFailed(f"Error retrieving device data: {err}") from err
        return data
