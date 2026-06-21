"""Home Assistant API via Supervisor proxy."""

from __future__ import annotations

import os

import httpx


class HomeAssistantError(Exception):
    """Raised when a Home Assistant API call fails."""


def add_todo_item(
    entity_id: str,
    item: str,
    description: str | None = None,
) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise HomeAssistantError(
            "Supervisor-Token nicht verfügbar — Add-on außerhalb von Home Assistant?"
        )

    base = os.environ.get("SUPERVISOR", "http://supervisor").rstrip("/")
    url = f"{base}/core/api/services/todo/add_item"
    payload: dict[str, str] = {
        "entity_id": entity_id,
        "item": item[:200],
    }
    if description:
        payload["description"] = description[:500]

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
            "Entity-ID in den Add-on-Optionen prüfen."
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
