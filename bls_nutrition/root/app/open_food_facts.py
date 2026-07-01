"""Open Food Facts barcode lookup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app import db

OFF_API = "https://world.openfoodfacts.org/api/v2/product/{barcode}"
OFF_SEARCH_API = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "BLS-Nutrition-HA-Addon/1.5"

OFF_SEARCH_FIELDS = (
    "code,product_name,product_name_de,brands,nutriments,"
    "nutrition_grades,nova_group,ecoscore_grade,environmental_score_grade"
)


def _parse_grade(raw: Any) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    grade = raw.strip().lower()
    if grade in ("a", "b", "c", "d", "e"):
        return grade
    return None


def _parse_nutriscore(product: dict[str, Any]) -> str | None:
    return _parse_grade(product.get("nutrition_grades") or product.get("nutrition_grade_fr"))


def _parse_nova_group(product: dict[str, Any]) -> int | None:
    raw = product.get("nova_group")
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 4 else None


def _parse_ecoscore(product: dict[str, Any]) -> str | None:
    return _parse_grade(
        product.get("ecoscore_grade") or product.get("environmental_score_grade")
    )


def _parse_off_scores(product: dict[str, Any]) -> dict[str, str | int | None]:
    return {
        "nutriscore": _parse_nutriscore(product),
        "nova_group": _parse_nova_group(product),
        "ecoscore": _parse_ecoscore(product),
    }


def _extract_image_url(product: dict[str, Any]) -> str | None:
    for key in ("image_front_url", "image_url", "image_small_url"):
        url = product.get(key)
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def fetch_product_image_url(barcode: str) -> str | None:
    barcode = barcode.strip()
    if not barcode:
        return None
    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            OFF_API.format(barcode=barcode),
            params={"fields": "image_front_url,image_url,image_small_url"},
            headers={"User-Agent": USER_AGENT},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
    if payload.get("status") != 1:
        return None
    return _extract_image_url(payload.get("product", {}))


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


def _product_to_search_result(
    product: dict[str, Any], language: str
) -> dict[str, Any] | None:
    barcode = str(product.get("code", "")).strip()
    if not barcode:
        return None
    name = (
        product.get("product_name_de")
        if language == "de"
        else product.get("product_name")
    ) or product.get("product_name") or product.get("product_name_de")
    if not name:
        return None
    brand = product.get("brands")
    scores = _parse_off_scores(product)
    return {
        "source": "off",
        "id": barcode,
        "name": name,
        "brand": brand,
        **scores,
    }


def _persist_off_product(
    conn,
    product: dict[str, Any],
    language: str,
) -> dict[str, Any] | None:
    result = _product_to_search_result(product, language)
    if not result:
        return None
    nutrients = _map_off_nutriments(product.get("nutriments", {}))
    scores = _parse_off_scores(product)
    db.save_off_product(
        conn,
        result["id"],
        result["name"],
        result.get("brand"),
        nutrients,
        **scores,
    )
    return result


def _fetch_off_search_api(
    conn,
    query: str,
    limit: int,
    language: str,
) -> list[dict[str, Any]]:
    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            OFF_SEARCH_API,
            params={
                "action": "process",
                "search_terms": query,
                "json": "true",
                "page_size": limit,
                "fields": OFF_SEARCH_FIELDS,
            },
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        payload = response.json()

    results: list[dict[str, Any]] = []
    for product in payload.get("products", []):
        item = _persist_off_product(conn, product, language)
        if item:
            results.append(item)
        if len(results) >= limit:
            break
    return results


def _merge_off_results(
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in primary + secondary:
        item_id = str(item.get("id", ""))
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


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

    if db.is_off_barcode_miss(conn, barcode, cache_ttl_days):
        return cached

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            OFF_API.format(barcode=barcode),
            headers={"User-Agent": USER_AGENT},
        )
        if response.status_code == 404:
            db.save_off_barcode_miss(conn, barcode)
            return cached
        response.raise_for_status()
        payload = response.json()

    if payload.get("status") != 1:
        db.save_off_barcode_miss(conn, barcode)
        return cached

    product = payload.get("product", {})
    nutrients = _map_off_nutriments(product.get("nutriments", {}))
    name = product.get("product_name") or product.get("product_name_de")
    brand = product.get("brands")

    scores = _parse_off_scores(product)
    db.save_off_product(conn, barcode, name, brand, nutrients, **scores)
    return db.get_off_product(conn, barcode)


def search_products(
    conn,
    query: str,
    limit: int = 10,
    *,
    enable_network: bool,
    language: str = "de",
    search_cache_ttl_days: int = 7,
) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    cached = db.get_off_search_cache(conn, query, language, limit, search_cache_ttl_days)
    if cached is not None:
        return cached

    local = db.search_off_products_local(conn, query, limit)
    if len(local) >= limit or not enable_network:
        if local:
            db.save_off_search_cache(conn, query, language, limit, local)
        return local

    try:
        api_results = _fetch_off_search_api(conn, query, limit, language)
    except httpx.HTTPError:
        if local:
            db.save_off_search_cache(conn, query, language, limit, local)
        return local

    merged = _merge_off_results(api_results, local, limit)
    db.save_off_search_cache(conn, query, language, limit, merged)
    return merged
