"""Home Assistant integration for BLS Nährwertdatenbank."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlsNutritionApiError, BlsNutritionClient
from .const import (
    DOMAIN,
    EVENT_CALCULATION_RESULT,
    EVENT_SEARCH_RESULT,
    SERVICE_CALCULATE_PORTION,
    SERVICE_CALCULATE_RECIPE,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_SAVE_CUSTOM_FOOD,
    SERVICE_SAVE_RECIPE,
    SERVICE_SEARCH_FOOD,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration via YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BLS Nährwertdatenbank from a config entry."""
    session = async_get_clientsession(hass)
    client = BlsNutritionClient(entry.data[CONF_HOST], entry.data[CONF_PORT], session)

    async def _update() -> dict[str, Any]:
        try:
            return await client.health()
        except BlsNutritionApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_update,
        update_interval=timedelta(minutes=5),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass, client)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _register_services(hass: HomeAssistant, client: BlsNutritionClient) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEARCH_FOOD):
        return

    async def handle_search(call: ServiceCall) -> None:
        results = await client.search_food(
            call.data["query"], call.data.get("limit", 20)
        )
        hass.bus.async_fire(
            EVENT_SEARCH_RESULT,
            {"query": call.data["query"], "results": results},
        )

    async def handle_barcode(call: ServiceCall) -> None:
        result = await client.lookup_barcode(call.data["barcode"])
        hass.bus.async_fire(EVENT_CALCULATION_RESULT, {"type": "barcode", "result": result})

    async def handle_portion(call: ServiceCall) -> None:
        result = await client.calculate_portion(
            call.data["source"], call.data["id"], call.data["amount_g"]
        )
        hass.bus.async_fire(
            EVENT_CALCULATION_RESULT, {"type": "portion", "result": result}
        )

    async def handle_recipe(call: ServiceCall) -> None:
        result = await client.calculate_recipe(
            call.data["ingredients"], call.data.get("servings", 1)
        )
        hass.bus.async_fire(
            EVENT_CALCULATION_RESULT, {"type": "recipe", "result": result}
        )

    async def handle_save_recipe(call: ServiceCall) -> None:
        await client.save_recipe(
            call.data["name"],
            call.data["ingredients"],
            call.data.get("servings", 1),
        )

    async def handle_save_custom_food(call: ServiceCall) -> None:
        await client.save_custom_food(
            call.data["name"],
            call.data["nutrients"],
            call.data.get("notes"),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_FOOD,
        handle_search,
        schema=voluptuous_schema_search(),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP_BARCODE,
        handle_barcode,
        schema=voluptuous_schema_barcode(),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CALCULATE_PORTION,
        handle_portion,
        schema=voluptuous_schema_portion(),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CALCULATE_RECIPE,
        handle_recipe,
        schema=voluptuous_schema_recipe(),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_RECIPE,
        handle_save_recipe,
        schema=voluptuous_schema_save_recipe(),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_CUSTOM_FOOD,
        handle_save_custom_food,
        schema=voluptuous_schema_save_custom_food(),
    )


def voluptuous_schema_search():
    import voluptuous as vol

    return vol.Schema(
        {
            vol.Required("query"): str,
            vol.Optional("limit", default=20): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        }
    )


def voluptuous_schema_barcode():
    import voluptuous as vol

    return vol.Schema({vol.Required("barcode"): str})


def voluptuous_schema_portion():
    import voluptuous as vol

    return vol.Schema(
        {
            vol.Required("source"): vol.In(["bls", "off", "custom"]),
            vol.Required("id"): str,
            vol.Required("amount_g"): vol.Coerce(float),
        }
    )


def voluptuous_schema_recipe():
    import voluptuous as vol

    return vol.Schema(
        {
            vol.Required("ingredients"): [dict],
            vol.Optional("servings", default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )


def voluptuous_schema_save_recipe():
    import voluptuous as vol

    return vol.Schema(
        {
            vol.Required("name"): str,
            vol.Required("ingredients"): [dict],
            vol.Optional("servings", default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )


def voluptuous_schema_save_custom_food():
    import voluptuous as vol

    return vol.Schema(
        {
            vol.Required("name"): str,
            vol.Required("nutrients"): dict,
            vol.Optional("notes"): str,
        }
    )
