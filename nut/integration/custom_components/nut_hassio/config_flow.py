"""Config flow for NUT Hass.io."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback

from .const import CONF_UPS_NAME, DEFAULT_HOST, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

try:
    from nut import PyNUTClient
except ImportError:  # pragma: no cover
    from PyNUT import PyNUTClient  # type: ignore[no-redef]


def _user_schema(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ups_name: str = "",
    username: str = "",
    password: str = "",
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_PORT, default=port): int,
            vol.Required(CONF_UPS_NAME, default=ups_name): str,
            vol.Optional(CONF_USERNAME, default=username): str,
            vol.Optional(CONF_PASSWORD, default=password): str,
        }
    )


class NutHassioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NUT Hass.io."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        host = DEFAULT_HOST
        port = DEFAULT_PORT
        ups_name = ""
        username = ""
        password = ""

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            ups_name = user_input[CONF_UPS_NAME]
            username = user_input.get(CONF_USERNAME) or ""
            password = user_input.get(CONF_PASSWORD) or ""

            try:
                await asyncio.to_thread(
                    self._validate_connection,
                    host,
                    port,
                    ups_name,
                    username or None,
                    password or None,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}:{ups_name}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"UPS {ups_name}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(host, port, ups_name, username, password),
            errors=errors,
        )

    @staticmethod
    def _validate_connection(
        host: str,
        port: int,
        ups_name: str,
        username: str | None,
        password: str | None,
    ) -> None:
        client = PyNUTClient(
            host=host,
            port=port,
            login=username,
            password=password,
            timeout=10,
        )
        names = client.GetUPSNames()
        if ups_name not in names:
            raise ValueError(f"UPS '{ups_name}' not found (available: {names})")
        client.GetUPSVars(ups_name)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return NutHassioOptionsFlow(config_entry)


class NutHassioOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return self.async_create_entry(title="", data=self.config_entry.options)
