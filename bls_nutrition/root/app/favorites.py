"""Favorite image resolution and OFF fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app import db, open_food_facts


def favorites_media_dir(data_dir: Path) -> Path:
    path = data_dir / "favorites"
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_image_file(data_dir: Path, image_path: str | None) -> Path | None:
    if not image_path:
        return None
    file_path = data_dir / image_path
    return file_path if file_path.is_file() else None


def resolve_off_image_url(
    favorite: dict[str, Any],
    *,
    enable_network: bool,
) -> str | None:
    if favorite.get("image_url"):
        return str(favorite["image_url"])
    barcode = favorite.get("barcode") or (
        favorite.get("source_id") if favorite.get("source") == "off" else None
    )
    if not barcode or not enable_network:
        return None
    return open_food_facts.fetch_product_image_url(str(barcode))


def enrich_favorite(
    favorite: dict[str, Any],
    *,
    data_dir: Path,
    enable_network: bool,
    conn,
) -> dict[str, Any]:
    enriched = dict(favorite)
    local_file = local_image_file(data_dir, favorite.get("image_path"))
    if local_file:
        enriched["has_local_image"] = True
        enriched["resolved_image"] = f"favorites/{favorite['id']}/image"
        return enriched

    off_url = resolve_off_image_url(favorite, enable_network=enable_network)
    if off_url and off_url != favorite.get("image_url"):
        updated = db.update_favorite(conn, int(favorite["id"]), image_url=off_url)
        if updated:
            enriched = dict(updated)
    enriched["has_local_image"] = False
    enriched["resolved_image"] = off_url
    return enriched
