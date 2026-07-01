"""Home Assistant integration for BLS Nährwertdatenbank."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlsNutritionApiError, BlsNutritionClient
from .const import (
    CONF_CONFIG_ENTRY_ID,
    CONF_DEFAULT_BARCODE_AMOUNT_G,
    DOMAIN,
    EVENT_CALCULATION_RESULT,
    EVENT_SEARCH_RESULT,
    SERVICE_ADD_FAVORITE,
    SERVICE_ADD_TO_TODO_LIST,
    SERVICE_CALCULATE_PORTION,
    SERVICE_CALCULATE_RECIPE,
    SERVICE_EXPORT_FAVORITES,
    SERVICE_IMPORT_FAVORITES,
    SERVICE_LIST_FAVORITES,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_REMOVE_FAVORITE,
    SERVICE_SAVE_CUSTOM_FOOD,
    SERVICE_SAVE_RECIPE,
    SERVICE_SEARCH_FOOD,
    SIGNAL_RESULT_UPDATED,
)
from .data import BlsRuntimeData

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_SERVICE_NAMES = (
    SERVICE_SEARCH_FOOD,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_CALCULATE_PORTION,
    SERVICE_CALCULATE_RECIPE,
    SERVICE_SAVE_RECIPE,
    SERVICE_SAVE_CUSTOM_FOOD,
    SERVICE_ADD_TO_TODO_LIST,
    SERVICE_ADD_FAVORITE,
    SERVICE_LIST_FAVORITES,
    SERVICE_REMOVE_FAVORITE,
    SERVICE_EXPORT_FAVORITES,
    SERVICE_IMPORT_FAVORITES,
)

_ENTRY_ID_FIELD = {vol.Optional(CONF_CONFIG_ENTRY_ID): str}


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

    async def handle_add_favorite(call: ServiceCall) -> dict[str, Any]:
        runtime, _entry_id = _get_runtime(hass, call)
        source = call.data["source"]
        item_id = call.data["id"]
        barcode = call.data.get("barcode")
        if source == "off" and not barcode:
            barcode = item_id
        favorite = await runtime.client.add_favorite(
            call.data["display_name"],
            source,
            item_id,
            barcode=barcode,
            brand=call.data.get("brand"),
            default_amount_g=float(call.data.get("default_amount_g", 100)),
        )
        return {"favorite": favorite}

    async def handle_list_favorites(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        favorites_list = await runtime.client.list_favorites()
        runtime.set_favorites_io(
            "list",
            favorites=favorites_list[:10],
            count=len(favorites_list),
        )
        _notify_updated(hass, entry_id)
        return {"favorites": favorites_list, "count": len(favorites_list)}

    async def handle_remove_favorite(call: ServiceCall) -> dict[str, Any]:
        runtime, _entry_id = _get_runtime(hass, call)
        result = await runtime.client.remove_favorite(int(call.data["favorite_id"]))
        return {"result": result}

    async def handle_export_favorites(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        export_format = call.data.get("format", "json")
        file_path = call.data.get("file_path")
        data = await runtime.client.export_favorites(export_format)
        if file_path:
            await asyncio.to_thread(Path(file_path).write_bytes, data)
        if export_format == "json":
            content: str | dict[str, Any] = json.loads(data.decode("utf-8"))
        else:
            content = data.decode("utf-8")
        await runtime.coordinator.async_request_refresh()
        favorites_count = runtime.coordinator.data.get("favorites_count")
        runtime.set_favorites_io(
            "export",
            format=export_format,
            file_path=file_path,
            favorites_count=favorites_count,
        )
        _notify_updated(hass, entry_id)
        response: dict[str, Any] = {
            "format": export_format,
            "content": content,
            "favorites_count": favorites_count,
        }
        if file_path:
            response["file_path"] = file_path
        return response

    async def handle_import_favorites(call: ServiceCall) -> dict[str, Any]:
        runtime, entry_id = _get_runtime(hass, call)
        file_path = call.data["file_path"]
        mode = call.data.get("mode", "merge")
        result = await runtime.client.import_favorites(file_path, mode=mode)
        await runtime.coordinator.async_request_refresh()
        favorites_count = runtime.coordinator.data.get("favorites_count")
        runtime.set_favorites_io(
            "import",
            file_path=file_path,
            mode=mode,
            imported=result.get("imported", 0),
            skipped=result.get("skipped", 0),
            errors=result.get("errors", []),
            favorites_count=favorites_count,
        )
        _notify_updated(hass, entry_id)
        return result

    if not hass.services.has_service(DOMAIN, SERVICE_SEARCH_FOOD):
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
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_LOOKUP_BARCODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOOKUP_BARCODE,
            handle_barcode,
            schema=vol.Schema(
                {
                    vol.Required("barcode"): str,
                    vol.Optional("amount_g"): vol.Coerce(float),
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_CALCULATE_PORTION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CALCULATE_PORTION,
            handle_portion,
            schema=vol.Schema(
                {
                    vol.Required("source"): vol.In(["bls", "off", "custom"]),
                    vol.Required("id"): str,
                    vol.Required("amount_g"): vol.Coerce(float),
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_CALCULATE_RECIPE):
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
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_SAVE_RECIPE):
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
                    **_ENTRY_ID_FIELD,
                }
            ),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_SAVE_CUSTOM_FOOD):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SAVE_CUSTOM_FOOD,
            handle_save_custom_food,
            schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("nutrients"): dict,
                    vol.Optional("notes"): str,
                    **_ENTRY_ID_FIELD,
                }
            ),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_ADD_TO_TODO_LIST):
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
                    **_ENTRY_ID_FIELD,
                }
            ),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_ADD_FAVORITE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_ADD_FAVORITE,
            handle_add_favorite,
            schema=vol.Schema(
                {
                    vol.Required("display_name"): str,
                    vol.Required("source"): vol.In(["bls", "off", "custom"]),
                    vol.Required("id"): str,
                    vol.Optional("barcode"): str,
                    vol.Optional("brand"): str,
                    vol.Optional("default_amount_g", default=100): vol.Coerce(float),
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_LIST_FAVORITES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LIST_FAVORITES,
            handle_list_favorites,
            schema=vol.Schema({**_ENTRY_ID_FIELD}),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_REMOVE_FAVORITE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REMOVE_FAVORITE,
            handle_remove_favorite,
            schema=vol.Schema(
                {
                    vol.Required("favorite_id"): vol.Coerce(int),
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_FAVORITES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_EXPORT_FAVORITES,
            handle_export_favorites,
            schema=vol.Schema(
                {
                    vol.Optional("format", default="json"): vol.In(["json", "csv"]),
                    vol.Optional("file_path"): str,
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_IMPORT_FAVORITES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_IMPORT_FAVORITES,
            handle_import_favorites,
            schema=vol.Schema(
                {
                    vol.Required("file_path"): str,
                    vol.Optional("mode", default="merge"): vol.In(["merge", "replace"]),
                    **_ENTRY_ID_FIELD,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )


def _unregister_services(hass: HomeAssistant) -> None:
    for service_name in _SERVICE_NAMES:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
