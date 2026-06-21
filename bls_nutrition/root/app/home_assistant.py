"""Home Assistant API via Supervisor proxy."""

from __future__ import annotations

import json
import logging
import os
import time

import httpx

_LOGGER = logging.getLogger(__name__)


class HomeAssistantError(Exception):
    """Raised when a Home Assistant API call fails."""


def _agent_log(
    location: str,
    message: str,
    data: dict[str, object],
    hypothesis_id: str,
) -> None:
    # #region agent log
    entry = {
        "sessionId": "92f7bb",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "hypothesisId": hypothesis_id,
        "runId": "run1",
    }
    line = json.dumps(entry, ensure_ascii=False)
    for path in (
        "/Users/henry/Projects/hassio-addons/.cursor/debug-92f7bb.log",
        "/data/bls_debug.ndjson",
    ):
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass
    _LOGGER.warning("[BLS_DEBUG] %s", line)
    # #endregion


def build_todo_item_text(name: str, description: str | None = None) -> str:
    """Build item text without using the HA description field.

    Many todo entities (e.g. the built-in shopping list) do not support
    SET_DESCRIPTION_ON_ITEM; sending ``description`` causes HA to return 500.
    """
    item = name.strip()
    if description:
        suffix = f" [{description}]"
        max_name = max(1, 200 - len(suffix))
        item = item[:max_name] + suffix
    return item[:200]


def add_todo_item(
    entity_id: str,
    item: str,
    description: str | None = None,
) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    item_text = build_todo_item_text(item, description)
    # #region agent log
    _agent_log(
        "home_assistant.py:add_todo_item:entry",
        "todo add_item called",
        {
            "entity_id": entity_id,
            "item_len": len(item_text),
            "metadata_in_item": description is not None,
            "has_supervisor_token": bool(token),
        },
        "H5",
    )
    # #endregion
    if not token:
        raise HomeAssistantError(
            "Supervisor-Token nicht verfügbar — Add-on außerhalb von Home Assistant?"
        )

    base = os.environ.get("SUPERVISOR", "http://supervisor").rstrip("/")
    url = f"{base}/core/api/services/todo/add_item"
    payload: dict[str, str] = {
        "entity_id": entity_id,
        "item": item_text,
    }

    # #region agent log
    _agent_log(
        "home_assistant.py:add_todo_item:request",
        "calling supervisor HA proxy",
        {
            "url": url,
            "payload_keys": sorted(payload.keys()),
            "sends_description_field": False,
        },
        "H5",
    )
    # #endregion

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as exc:
        # #region agent log
        _agent_log(
            "home_assistant.py:add_todo_item:request_error",
            "supervisor request failed",
            {"error_type": type(exc).__name__, "error": str(exc)},
            "H4",
        )
        # #endregion
        raise HomeAssistantError(f"Verbindung zu Home Assistant fehlgeschlagen: {exc}") from exc

    # #region agent log
    _agent_log(
        "home_assistant.py:add_todo_item:response",
        "supervisor HA proxy response",
        {
            "status_code": response.status_code,
            "body_preview": response.text.strip()[:300],
        },
        "H5",
    )
    # #endregion

    if response.status_code == 404:
        raise HomeAssistantError(
            f"To-do-Liste nicht gefunden: {entity_id}. "
            "Entity-ID in den Add-on-Optionen prüfen (z. B. todo.shopping_list)."
        )
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise HomeAssistantError(
            f"Home Assistant hat den Eintrag abgelehnt ({response.status_code}): {detail}"
        )


def build_todo_description(barcode: str | None, brand: str | None) -> str | None:
    parts = ["OFF"]
    if barcode:
        parts.append(barcode.strip())
    if brand:
        parts.append(brand.strip())
    return " · ".join(parts) if len(parts) > 1 else None
