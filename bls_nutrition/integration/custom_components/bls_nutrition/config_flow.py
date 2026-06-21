"""Config flow for BLS Nährwertdatenbank."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BlsNutritionApiError, BlsNutritionClient
from .const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class BlsNutritionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BLS Nährwertdatenbank."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = BlsNutritionClient(
                user_input[CONF_HOST], user_input[CONF_PORT], session
            )
            try:
                health = await client.health()
            except (BlsNutritionApiError, aiohttp.ClientError) as err:
                _LOGGER.error("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                title = f"BLS Nährwert ({health.get('food_count', 0)} Lebensmittel)"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
