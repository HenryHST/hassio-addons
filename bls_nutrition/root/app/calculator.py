"""Portion and recipe nutrient calculations."""

from __future__ import annotations

from typing import Any

from app import db, diabetes


def scale_nutrients(
    nutrients_per_100g: dict[str, float | None], amount_g: float
) -> dict[str, float | None]:
    factor = amount_g / 100.0
    return {
        code: round(value * factor, 4) if value is not None else None
        for code, value in nutrients_per_100g.items()
    }


def sum_nutrients(nutrient_lists: list[dict[str, float | None]]) -> dict[str, float | None]:
    totals: dict[str, float] = {}
    for nutrients in nutrient_lists:
        for code, value in nutrients.items():
            if value is None:
                continue
            totals[code] = totals.get(code, 0.0) + value
    return {code: round(value, 4) for code, value in totals.items()}


def calculate_portion(
    conn,
    source: str,
    item_id: str,
    amount_g: float,
    language: str = "de",
) -> dict[str, Any]:
    per_100g = db.get_nutrients_per_100g(conn, source, item_id)
    if not per_100g and source != "custom":
        raise ValueError(f"Food not found: {source}:{item_id}")

    scaled = scale_nutrients(per_100g, amount_g)
    key_nutrients = db.get_key_nutrients(scaled)
    diabetes_units = diabetes.compute_diabetes_units(key_nutrients)

    name = None
    nutriscore = None
    nova_group = None
    ecoscore = None
    if source == "bls":
        name = db.get_food_name(conn, item_id, language)
    elif source == "custom":
        row = db.get_custom_food(conn, int(item_id))
        name = row["name"] if row else None
    elif source == "off":
        row = db.get_off_product(conn, item_id)
        if row:
            name = row["name"]
            nutriscore = row.get("nutriscore")
            nova_group = row.get("nova_group")
            ecoscore = row.get("ecoscore")

    return {
        "source": source,
        "id": item_id,
        "name": name,
        "amount_g": amount_g,
        "nutrients": key_nutrients,
        "all_nutrients": scaled,
        "diabetes": diabetes_units,
        "nutriscore": nutriscore,
        "nova_group": nova_group,
        "ecoscore": ecoscore,
    }


def calculate_recipe(
    conn,
    ingredients: list[dict[str, Any]],
    servings: int = 1,
    language: str = "de",
) -> dict[str, Any]:
    scaled_lists: list[dict[str, float | None]] = []
    ingredient_details: list[dict[str, Any]] = []

    for ingredient in ingredients:
        portion = calculate_portion(
            conn,
            ingredient["source"],
            ingredient["id"],
            float(ingredient["amount_g"]),
            language,
        )
        scaled_lists.append(portion["all_nutrients"])
        ingredient_details.append(
            {
                "source": portion["source"],
                "id": portion["id"],
                "name": portion["name"],
                "amount_g": portion["amount_g"],
                "diabetes": portion["diabetes"],
            }
        )

    total = sum_nutrients(scaled_lists)
    key_nutrients = db.get_key_nutrients(total)
    diabetes_units = diabetes.compute_diabetes_units(key_nutrients)

    if servings > 1:
        per_serving = {
            code: round(value / servings, 4) if value is not None else None
            for code, value in key_nutrients.items()
        }
        diabetes_per_serving = diabetes.compute_diabetes_units(per_serving)
    else:
        per_serving = key_nutrients
        diabetes_per_serving = diabetes_units

    return {
        "servings": servings,
        "nutrients": key_nutrients,
        "nutrients_per_serving": per_serving,
        "diabetes": diabetes_units,
        "diabetes_per_serving": diabetes_per_serving,
        "ingredients": ingredient_details,
    }
