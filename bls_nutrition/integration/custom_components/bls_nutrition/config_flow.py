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
from .const import CONF_DEFAULT_BARCODE_AMOUNT_G, DEFAULT_HOST, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _user_schema(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_PORT, default=port): int,
        }
    )


class BlsNutritionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BLS Nährwertdatenbank."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        host = DEFAULT_HOST
        port = DEFAULT_PORT
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            session = async_get_clientsession(self.hass)
            client = BlsNutritionClient(host, port, session)
            try:
                health = await client.health()
            except (BlsNutritionApiError, aiohttp.ClientError) as err:
                _LOGGER.error("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                title = f"BLS Nährwert ({health.get('food_count', 0)} Lebensmittel)"
                return self.async_create_entry(
                    title=title,
                    data=user_input,
                    options={CONF_DEFAULT_BARCODE_AMOUNT_G: 100.0},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(host, port),
            errors=errors,
            description_placeholders={
                "default_host": DEFAULT_HOST,
                "default_port": str(DEFAULT_PORT),
            },
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return BlsNutritionOptionsFlow(config_entry)


class BlsNutritionOptionsFlow(config_entries.OptionsFlow):
    """Handle options for BLS Nährwertdatenbank."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            default_amount = user_input[CONF_DEFAULT_BARCODE_AMOUNT_G]
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_HOST: host, CONF_PORT: port},
                options={CONF_DEFAULT_BARCODE_AMOUNT_G: default_amount},
            )
            return self.async_create_entry(title="", data={})

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, DEFAULT_HOST),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): int,
                    vol.Required(
                        CONF_DEFAULT_BARCODE_AMOUNT_G,
                        default=options.get(CONF_DEFAULT_BARCODE_AMOUNT_G, 100.0),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
                }
            ),
        )
