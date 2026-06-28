"""Home Assistant integration for the NUT Hass.io add-on."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, callback

from .const import CONF_UPS_NAME, DOMAIN, EVENT_NUT_UPS, NOTIFY_STATUSES
from .coordinator import NutHassioCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration via YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NUT Hass.io from a config entry."""
    coordinator = NutHassioCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    @callback
    def _handle_ups_event(event) -> None:
        if event.data.get("ups_name") != entry.data[CONF_UPS_NAME]:
            return
        notify_type = event.data.get("notify_type")
        if notify_type not in NOTIFY_STATUSES:
            return
        coordinator.apply_notify(notify_type)
        if coordinator.data:
            coordinator.async_set_updated_data(
                {
                    **coordinator.data,
                    "status": notify_type,
                }
            )

    entry.async_on_unload(
        hass.bus.async_listen(EVENT_NUT_UPS, _handle_ups_event)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
