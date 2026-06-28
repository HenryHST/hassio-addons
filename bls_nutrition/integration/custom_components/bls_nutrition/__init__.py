"""Home Assistant integration for BLS Nährwertdatenbank."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlsNutritionApiError, BlsNutritionClient
from .const import (
    CONF_CONFIG_ENTRY_ID,
    CONF_DEFAULT_BARCODE_AMOUNT_G,
    DOMAIN,
    EVENT_CALCULATION_RESULT,
    EVENT_SEARCH_RESULT,
    SERVICE_ADD_TO_TODO_LIST,
    SERVICE_CALCULATE_PORTION,
    SERVICE_CALCULATE_RECIPE,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_SAVE_CUSTOM_FOOD,
    SERVICE_SAVE_RECIPE,
    SERVICE_SEARCH_FOOD,
    SIGNAL_RESULT_UPDATED,
)
from .data import BlsRuntimeData

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

_SERVICE_NAMES = (
    SERVICE_SEARCH_FOOD,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_CALCULATE_PORTION,
    SERVICE_CALCULATE_RECIPE,
    SERVICE_SAVE_RECIPE,
    SERVICE_SAVE_CUSTOM_FOOD,
    SERVICE_ADD_TO_TODO_LIST,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration via YAML is not supported."""
    return True


def _get_runtime(hass: HomeAssistant, call: ServiceCall) -> tuple[BlsRuntimeData, str]:
    domain_data: dict[str, BlsRuntimeData] = hass.data.get(DOMAIN, {})
    if not domain_data:
        raise ServiceValidationError("BLS integration is not configured")

    entry_id = call.data.get(CONF_CONFIG_ENTRY_ID)
    if entry_id:
        runtime = domain_data.get(entry_id)
        if runtime is None:
            raise ServiceValidationError(f"Unknown config entry: {entry_id}")
        return runtime, entry_id

    if len(domain_data) == 1:
        entry_id = next(iter(domain_data))
        return domain_data[entry_id], entry_id

    raise ServiceValidationError(
        "config_entry_id is required when multiple BLS integrations are configured"
    )


def _notify_updated(hass: HomeAssistant, entry_id: str) -> None:
    dispatcher_send(hass, SIGNAL_RESULT_UPDATED, entry_id)


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

    runtime = BlsRuntimeData(client=client, coordinator=coordinator)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN):
            _unregister_services(hass)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEARCH_FOOD):
        return

    entry_id_schema = vol.Optional(CONF_CONFIG_ENTRY_ID): str

    async def handle_search(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        results = await runtime.client.search_food(
            call.data["query"], call.data.get("limit", 20)
        )
        runtime.set_search(call.data["query"], results)
        _notify_updated(hass, entry_id)
        hass.bus.async_fire(
            EVENT_SEARCH_RESULT,
            {"query": call.data["query"], "results": results},
        )
        return {"query": call.data["query"], "results": results}

    async def handle_barcode(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        entry = hass.config_entries.async_get_entry(entry_id)
        default_amount = 100.0
        if entry is not None:
            default_amount = float(
                entry.options.get(CONF_DEFAULT_BARCODE_AMOUNT_G, default_amount)
            )
        amount_g = float(call.data.get("amount_g", default_amount))
        product = await runtime.client.lookup_barcode(call.data["barcode"])
        result = await runtime.client.calculate_portion("off", product["id"], amount_g)
        runtime.set_calculation("barcode", result)
        _notify_updated(hass, entry_id)
        hass.bus.async_fire(
            EVENT_CALCULATION_RESULT, {"type": "barcode", "result": result}
        )
        return {"product": product, "result": result}

    async def handle_portion(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        result = await runtime.client.calculate_portion(
            call.data["source"], call.data["id"], call.data["amount_g"]
        )
        runtime.set_calculation("portion", result)
        _notify_updated(hass, entry_id)
        hass.bus.async_fire(
            EVENT_CALCULATION_RESULT, {"type": "portion", "result": result}
        )
        return {"result": result}

    async def handle_recipe(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        result = await runtime.client.calculate_recipe(
            call.data["ingredients"], call.data.get("servings", 1)
        )
        runtime.set_calculation("recipe", result)
        _notify_updated(hass, entry_id)
        hass.bus.async_fire(
            EVENT_CALCULATION_RESULT, {"type": "recipe", "result": result}
        )
        return {"result": result}

    async def handle_save_recipe(call: ServiceCall) -> None:
        runtime, _entry_id = _get_runtime(hass, call)
        await runtime.client.save_recipe(
            call.data["name"],
            call.data["ingredients"],
            call.data.get("servings", 1),
        )

    async def handle_save_custom_food(call: ServiceCall) -> None:
        runtime, _entry_id = _get_runtime(hass, call)
        await runtime.client.save_custom_food(
            call.data["name"],
            call.data["nutrients"],
            call.data.get("notes"),
        )

    async def handle_add_to_todo_list(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id", "todo.shopping_list")
        name = call.data["name"]
        desc_parts = ["OFF"]
        if call.data.get("barcode"):
            desc_parts.append(str(call.data["barcode"]).strip())
        if call.data.get("brand"):
            desc_parts.append(str(call.data["brand"]).strip())
        description = " · ".join(desc_parts) if len(desc_parts) > 1 else None
        item_text = name.strip()
        if description:
            suffix = f" [{description}]"
            max_name = max(1, 200 - len(suffix))
            item_text = name.strip()[:max_name] + suffix
        await hass.services.async_call(
            "todo",
            "add_item",
            {"item": item_text[:200]},
            target={"entity_id": entity_id},
            blocking=True,
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_FOOD,
        handle_search,
        schema=vol.Schema(
            {
                vol.Required("query"): str,
                vol.Optional("limit", default=20): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=100)
                ),
                entry_id_schema,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP_BARCODE,
        handle_barcode,
        schema=vol.Schema(
            {
                vol.Required("barcode"): str,
                vol.Optional("amount_g"): vol.Coerce(float),
                entry_id_schema,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CALCULATE_PORTION,
        handle_portion,
        schema=vol.Schema(
            {
                vol.Required("source"): vol.In(["bls", "off", "custom"]),
                vol.Required("id"): str,
                vol.Required("amount_g"): vol.Coerce(float),
                entry_id_schema,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CALCULATE_RECIPE,
        handle_recipe,
        schema=vol.Schema(
            {
                vol.Required("ingredients"): [dict],
                vol.Optional("servings", default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                entry_id_schema,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_RECIPE,
        handle_save_recipe,
        schema=vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("ingredients"): [dict],
                vol.Optional("servings", default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                entry_id_schema,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_CUSTOM_FOOD,
        handle_save_custom_food,
        schema=vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("nutrients"): dict,
                vol.Optional("notes"): str,
                entry_id_schema,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_TO_TODO_LIST,
        handle_add_to_todo_list,
        schema=vol.Schema(
            {
                vol.Required("name"): str,
                vol.Optional("barcode"): str,
                vol.Optional("brand"): str,
                vol.Optional("entity_id", default="todo.shopping_list"): str,
                entry_id_schema,
            }
        ),
    )


def _unregister_services(hass: HomeAssistant) -> None:
    for service_name in _SERVICE_NAMES:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
