"""Home Assistant API via Supervisor proxy."""

from __future__ import annotations

import os

import httpx


class HomeAssistantError(Exception):
    """Raised when a Home Assistant API call fails."""


def _supervisor_auth() -> tuple[str, str]:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise HomeAssistantError(
            "Supervisor-Token nicht verfügbar — Add-on außerhalb von Home Assistant?"
        )
    base = os.environ.get("SUPERVISOR", "http://supervisor").rstrip("/")
    return base, token


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
    base, token = _supervisor_auth()
    url = f"{base}/core/api/services/todo/add_item"
    payload: dict[str, str] = {
        "entity_id": entity_id,
        "item": build_todo_item_text(item, description),
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as exc:
        raise HomeAssistantError(f"Verbindung zu Home Assistant fehlgeschlagen: {exc}") from exc

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


def get_home_location() -> dict[str, float | str]:
    base, token = _supervisor_auth()
    url = f"{base}/core/api/config"
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.RequestError as exc:
        raise HomeAssistantError(f"Verbindung zu Home Assistant fehlgeschlagen: {exc}") from exc
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason_phrase
        raise HomeAssistantError(
            f"Home Assistant Standort konnte nicht gelesen werden ({response.status_code}): {detail}"
        )
    try:
        payload = response.json()
        latitude = float(payload["latitude"])
        longitude = float(payload["longitude"])
        time_zone = str(payload.get("time_zone") or "UTC")
    except (KeyError, TypeError, ValueError) as exc:
        raise HomeAssistantError("Home Assistant liefert keine gueltigen Standortdaten.") from exc
    return {
        "latitude": latitude,
        "longitude": longitude,
        "time_zone": time_zone,
    }


def get_home_coordinates() -> tuple[float, float]:
    location = get_home_location()
    return float(location["latitude"]), float(location["longitude"])


def build_todo_description(barcode: str | None, brand: str | None) -> str | None:
    parts = ["OFF"]
    if barcode:
        parts.append(barcode.strip())
    if brand:
        parts.append(brand.strip())
    return " · ".join(parts) if len(parts) > 1 else None
