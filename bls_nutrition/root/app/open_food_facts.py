"""Open Food Facts barcode lookup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app import db

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}"
OFF_SEARCH_API = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "BLS-Nutrition-HA-Addon/1.2"


def _map_off_nutriments(nutriments: dict[str, Any]) -> dict[str, float | None]:
    mapping = {
        "energy_kcal": nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g"),
        "energy_kj": nutriments.get("energy-kj_100g"),
        "fat": nutriments.get("fat_100g"),
        "proteins": nutriments.get("proteins_100g"),
        "carbohydrates": nutriments.get("carbohydrates_100g"),
        "sugars": nutriments.get("sugars_100g"),
        "fiber": nutriments.get("fiber_100g"),
        "salt": nutriments.get("salt_100g"),
        "sodium": nutriments.get("sodium_100g"),
    }
    result: dict[str, float | None] = {}
    for key, value in mapping.items():
        if value is None:
            result[key] = None
        else:
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                result[key] = None

    if result.get("energy_kcal") is None and result.get("energy_kj"):
        result["energy_kcal"] = round(result["energy_kj"] / 4.184, 2)

    result["CHO"] = result.get("carbohydrates")
    result["FAT"] = result.get("fat")
    result["PROT625"] = result.get("proteins")
    result["FIBT"] = result.get("fiber")
    result["NACL"] = result.get("salt")
    result["ENERCC"] = result.get("energy_kcal")
    result["ENERCJ"] = result.get("energy_kj")
    return result


def _is_cache_valid(fetched_at: str, ttl_days: int) -> bool:
    try:
        fetched = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False
    return fetched > datetime.now(timezone.utc) - timedelta(days=ttl_days)


def lookup_barcode(
    conn,
    barcode: str,
    *,
    enable_network: bool,
    cache_ttl_days: int,
) -> dict[str, Any] | None:
    barcode = barcode.strip()
    if not barcode:
        return None

    cached = db.get_off_product(conn, barcode)
    if cached and _is_cache_valid(cached["fetched_at"], cache_ttl_days):
        return cached

    if not enable_network:
        return cached

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            OFF_API.format(barcode=barcode),
            headers={"User-Agent": USER_AGENT},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()

    if payload.get("status") != 1:
        return None

    product = payload.get("product", {})
    nutrients = _map_off_nutriments(product.get("nutriments", {}))
    name = product.get("product_name") or product.get("product_name_de")
    brand = product.get("brands")

    db.save_off_product(conn, barcode, name, brand, nutrients)
    return db.get_off_product(conn, barcode)


def search_products(
    conn,
    query: str,
    limit: int = 10,
    *,
    enable_network: bool,
    language: str = "de",
) -> list[dict[str, Any]]:
    query = query.strip()
    if not query or not enable_network:
        return []

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            OFF_SEARCH_API,
            params={
                "action": "process",
                "search_terms": query,
                "json": "true",
                "page_size": limit,
                "fields": "code,product_name,product_name_de,brands,nutriments",
            },
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        payload = response.json()

    results: list[dict[str, Any]] = []
    for product in payload.get("products", []):
        barcode = str(product.get("code", "")).strip()
        if not barcode:
            continue
        name = (
            product.get("product_name_de")
            if language == "de"
            else product.get("product_name")
        ) or product.get("product_name") or product.get("product_name_de")
        if not name:
            continue
        brand = product.get("brands")
        nutrients = _map_off_nutriments(product.get("nutriments", {}))
        db.save_off_product(conn, barcode, name, brand, nutrients)
        results.append(
            {
                "source": "off",
                "id": barcode,
                "name": name,
                "brand": brand,
            }
        )
        if len(results) >= limit:
            break
    return results
