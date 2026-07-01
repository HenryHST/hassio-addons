"""Favorites import/export serialization."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
CSV_COLUMNS = (
    "display_name",
    "source",
    "source_id",
    "barcode",
    "brand",
    "default_amount_g",
    "image_url",
    "sort_order",
)
VALID_SOURCES = frozenset({"bls", "off", "custom"})


def _normalize_item(raw: dict[str, Any]) -> dict[str, Any]:
    source = str(raw.get("source", "")).strip()
    source_id = str(raw.get("source_id") or raw.get("id", "")).strip()
    display_name = str(raw.get("display_name", "")).strip()
    if not source or source not in VALID_SOURCES:
        raise ValueError(f"Ungültige Quelle: {source!r}")
    if not source_id:
        raise ValueError("source_id fehlt")
    if not display_name:
        raise ValueError("display_name fehlt")
    amount = raw.get("default_amount_g", 100)
    try:
        default_amount_g = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError("default_amount_g ungültig") from exc
    if default_amount_g <= 0:
        raise ValueError("default_amount_g muss > 0 sein")
    barcode = raw.get("barcode")
    brand = raw.get("brand")
    image_url = raw.get("image_url")
    sort_order = raw.get("sort_order", 0)
    try:
        sort_order_int = int(sort_order)
    except (TypeError, ValueError):
        sort_order_int = 0
    if source == "off" and not barcode:
        barcode = source_id
    return {
        "display_name": display_name,
        "source": source,
        "source_id": source_id,
        "barcode": str(barcode).strip() if barcode else None,
        "brand": str(brand).strip() if brand else None,
        "default_amount_g": default_amount_g,
        "image_url": str(image_url).strip() if image_url else None,
        "sort_order": sort_order_int,
    }


def export_json_payload(favorites: list[dict[str, Any]], addon_version: str) -> dict[str, Any]:
    items = []
    for fav in favorites:
        items.append(
            {
                "display_name": fav["display_name"],
                "source": fav["source"],
                "source_id": fav["source_id"],
                "barcode": fav.get("barcode"),
                "brand": fav.get("brand"),
                "default_amount_g": fav["default_amount_g"],
                "image_url": fav.get("image_url"),
                "sort_order": fav.get("sort_order", 0),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "addon_version": addon_version,
        "favorites": items,
    }


def export_json_bytes(favorites: list[dict[str, Any]], addon_version: str) -> bytes:
    payload = export_json_payload(favorites, addon_version)
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def export_csv_bytes(favorites: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for fav in favorites:
        writer.writerow(
            {
                "display_name": fav["display_name"],
                "source": fav["source"],
                "source_id": fav["source_id"],
                "barcode": fav.get("barcode") or "",
                "brand": fav.get("brand") or "",
                "default_amount_g": fav["default_amount_g"],
                "image_url": fav.get("image_url") or "",
                "sort_order": fav.get("sort_order", 0),
            }
        )
    return buffer.getvalue().encode("utf-8")


def parse_import_bytes(data: bytes, filename: str = "") -> list[dict[str, Any]]:
    name = filename.lower()
    if name.endswith(".csv") or data.strip().startswith(b"display_name,"):
        return _parse_csv(data)
    return _parse_json(data)


def _parse_json(data: bytes) -> list[dict[str, Any]]:
    payload = json.loads(data.decode("utf-8"))
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict) and "favorites" in payload:
        raw_items = payload["favorites"]
    else:
        raise ValueError("Ungültiges JSON-Format")
    if not isinstance(raw_items, list):
        raise ValueError("favorites muss eine Liste sein")
    return [_normalize_item(item) for item in raw_items if isinstance(item, dict)]


def _parse_csv(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV ohne Kopfzeile")
    items: list[dict[str, Any]] = []
    for row in reader:
        if not any((value or "").strip() for value in row.values()):
            continue
        item = {key: (row.get(key) or "").strip() or None for key in CSV_COLUMNS}
        if item.get("default_amount_g") is None:
            item["default_amount_g"] = 100
        items.append(_normalize_item(item))
    return items
