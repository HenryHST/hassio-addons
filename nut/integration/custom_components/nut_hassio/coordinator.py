"""Data update coordinator for NUT Hass.io."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPS_NAME, DOMAIN, NOTIFY_STATUSES, POLL_INTERVAL_SECONDS
from .status import map_ups_status

_LOGGER = logging.getLogger(__name__)

try:
    from nut import PyNUTClient
except ImportError:  # pragma: no cover - runtime dependency
    from PyNUT import PyNUTClient  # type: ignore[no-redef]


class NutHassioCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch UPS variables from upsd."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self._host = entry.data[CONF_HOST]
        self._port = entry.data[CONF_PORT]
        self._username = entry.data.get(CONF_USERNAME)
        self._password = entry.data.get(CONF_PASSWORD)
        self._ups_name = entry.data[CONF_UPS_NAME]
        self._last_notify: str | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL_SECONDS),
        )

    @property
    def ups_name(self) -> str:
        return self._ups_name

    def apply_notify(self, notify_type: str) -> None:
        """Apply immediate status from nut.ups_event."""
        if notify_type in NOTIFY_STATUSES:
            self._last_notify = notify_type

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            variables = await asyncio.to_thread(self._fetch_vars)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with NUT server: {err}") from err

        raw_status = variables.get("ups.status", "")
        mapped = map_ups_status(raw_status)
        status = self._last_notify or mapped

        return {
            "raw_status": raw_status,
            "status": status,
            "variables": variables,
        }

    def _fetch_vars(self) -> dict[str, str]:
        client = PyNUTClient(
            host=self._host,
            port=self._port,
            login=self._username,
            password=self._password,
            timeout=10,
        )
        return client.GetUPSVars(self._ups_name)
