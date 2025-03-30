"""Config flow for Ecactus Ecos integration."""

import logging
from typing import Any

import ecactus
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_DATACENTER, CONF_HOME_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_USERNAME, description={"suggested_value": "email@domain.com"}
        ): str,
        vol.Required(CONF_PASSWORD, description={"suggested_value": "1234"}): str,
        vol.Required(CONF_DATACENTER): vol.In(["EU", "AU", "CN"]),
    }
)


class EcactusEcosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow class."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    _ecos_session: ecactus.AsyncEcos

    def __init__(self) -> None:
        """Initialise config flow."""
        self.data: dict[str, Any] = {}

    async def _validate_input(self, data: dict[str, Any]) -> None:
        """Validate the user input allows us to connect."""
        try:
            self._ecos_session = ecactus.AsyncEcos(datacenter=data[CONF_DATACENTER])
            await self._ecos_session.login(data[CONF_USERNAME], data[CONF_PASSWORD])
        # TODO: refining exception
        except Exception as err:
            raise InvalidAuth from err

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle credential request step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # The form has been filled in and submitted, so process the data provided.
            user_input[CONF_DATACENTER] = "EU"
            try:
                await self._validate_input(user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                self.data = user_input
                return await self.async_step_home()

        # Show initial form
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle home selection step."""
        # List available homes for selection
        home_list = await self._ecos_session.get_homes()

        if len(home_list) == 0:
            return self.async_abort(reason="no_homes")

        if user_input is None:
            if len(home_list) > 1:
                # 2 or more homes, so show the selection form
                homes = {home.id: home.name for home in home_list}
                data_schema = vol.Schema({vol.Required(CONF_HOME_ID): vol.In(homes)})
                return self.async_show_form(step_id="home", data_schema=data_schema)

            # single home => mark it as selected
            user_input = {CONF_HOME_ID: home_list[0].id}

        # The home has been selected
        user_input[CONF_NAME] = "Default"
        for home in home_list:
            if home.id == user_input[CONF_HOME_ID]:
                user_input[CONF_NAME] = home.name
                break
        await self.async_set_unique_id(user_input[CONF_HOME_ID])
        self._abort_if_unique_id_configured()
        self.data.update(user_input)
        return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
