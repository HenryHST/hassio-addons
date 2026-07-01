"""FastAPI application."""

from __future__ import annotations

import html as html_module
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import bootstrap, calculator, db, favorites, home_assistant, open_food_facts, opening_hours_display, overpass
from app.models import (
    CalculationResult,
    CustomFoodCreate,
    CustomFoodUpdate,
    CustomRecipeCreate,
    DiabetesUnits,
    FavoriteCreate,
    FavoriteUpdate,
    PortionRequest,
    RecipeRequest,
    TodoListItemRequest,
)
from app.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if bootstrap.prepare_database():
        thread = threading.Thread(
            target=bootstrap.run_bls_import,
            name="bls-import",
            daemon=True,
        )
        thread.start()
    yield


app = FastAPI(
    title="BLS Nährwertdatenbank",
    version="1.8.2",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _settings() -> Settings:
    return get_settings()


def _diabetes_model(data: dict[str, Any]) -> DiabetesUnits:
    return DiabetesUnits(**data)


def _require_favorites_enabled(settings: Settings) -> None:
    if not settings.favorites_enabled:
        raise HTTPException(status_code=403, detail="Favoriten sind deaktiviert")


def _enrich_favorites_list(conn: Any, settings: Settings) -> list[dict[str, Any]]:
    items = db.list_favorites(conn)
    return [
        favorites.enrich_favorite(
            item,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )
        for item in items
    ]


@app.get("/health")
def health() -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        return {
            "status": "ok",
            "addon_version": settings.addon_version,
            "database_engine": db.get_meta(conn, "database_engine") or "duckdb",
            "database_status": db.get_database_status(conn),
            "bls_version": db.get_meta(conn, "bls_version") or settings.bls_version,
            "imported_at": db.get_meta(conn, "imported_at"),
            "food_count": db.food_count(conn),
            "off_products_count": db.off_products_count(conn),
            "open_food_facts_enabled": settings.enable_open_food_facts,
            "search_layout": settings.search_layout,
            "search_recents_enabled": settings.search_recents_enabled,
            "todo_list_enabled": settings.todo_list_enabled,
            "todo_list_entity_id": settings.todo_list_entity_id,
            "map_enabled": settings.map_enabled,
            "map_radius_km": settings.map_radius_km,
            "favorites_enabled": settings.favorites_enabled,
            "favorites_count": db.favorites_count(conn),
        }


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    ingress_path = request.headers.get("x-ingress-path")
    if ingress_path:
        base_href = ingress_path if ingress_path.endswith("/") else f"{ingress_path}/"
        base_tag = f'<base href="{html_module.escape(base_href, quote=True)}">'
        html = html.replace("<head>", f"<head>{base_tag}", 1)
    return HTMLResponse(html)


@app.get("/foods/search/off")
def search_off_products(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, Any]]:
    settings = _settings()
    if not settings.enable_open_food_facts:
        return []
    with db.get_connection(settings.db_path) as conn:
        return open_food_facts.search_products(
            conn,
            q,
            limit,
            enable_network=settings.enable_open_food_facts,
            language=settings.language,
            search_cache_ttl_days=settings.off_search_cache_ttl_days,
        )


@app.get("/foods/search")
def search_foods(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, Any]]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        return db.search_foods(conn, q, limit, settings.language)


@app.get("/foods/barcode/{barcode}")
def lookup_barcode(barcode: str) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        product = open_food_facts.lookup_barcode(
            conn,
            barcode,
            enable_network=settings.enable_open_food_facts,
            cache_ttl_days=settings.off_cache_ttl_days,
        )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    key = db.get_key_nutrients(product["nutrients"])
    return {**product, "nutrients": key, "all_nutrients": product["nutrients"]}


@app.post("/todo-list/items")
def add_todo_list_item(payload: TodoListItemRequest) -> dict[str, str]:
    settings = _settings()
    if not settings.todo_list_enabled:
        raise HTTPException(status_code=403, detail="Einkaufsliste-Import ist deaktiviert")
    description = home_assistant.build_todo_description(payload.barcode, payload.brand)
    try:
        home_assistant.add_todo_item(
            settings.todo_list_entity_id,
            payload.name.strip(),
            description,
        )
    except home_assistant.HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"status": "added", "item": payload.name}


@app.get("/foods/{bls_code}")
def get_food(bls_code: str) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        name = db.get_food_name(conn, bls_code, settings.language)
        if not name:
            raise HTTPException(status_code=404, detail="Food not found")
        nutrients = db.get_nutrients_per_100g(conn, "bls", bls_code)
        key = db.get_key_nutrients(nutrients)
        return {
            "source": "bls",
            "id": bls_code,
            "name": name,
            "nutrients": key,
            "all_nutrients": nutrients,
        }


@app.get("/map/supermarkets")
def map_supermarkets(radius_km: int | None = Query(default=None, ge=1, le=50)) -> dict[str, Any]:
    settings = _settings()
    if not settings.map_enabled:
        raise HTTPException(status_code=403, detail="Map-Funktion ist deaktiviert.")
    effective_radius = radius_km if radius_km is not None else settings.map_radius_km
    effective_radius = max(1, min(50, int(effective_radius)))
    try:
        location = home_assistant.get_home_location()
    except home_assistant.HomeAssistantError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    latitude = float(location["latitude"])
    longitude = float(location["longitude"])
    time_zone = str(location["time_zone"])
    try:
        supermarkets = overpass.find_supermarkets(latitude, longitude, effective_radius)
    except overpass.OverpassError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    ctx = opening_hours_display.get_location_context(
        latitude, longitude, time_zone, settings.data_dir
    )
    supermarkets = opening_hours_display.enrich_map_items(supermarkets, ctx)
    return {
        "center": {"lat": latitude, "lon": longitude},
        "radius_km": effective_radius,
        "count": len(supermarkets),
        "items": supermarkets,
    }


@app.get("/favorites")
def list_favorites() -> list[dict[str, Any]]:
    settings = _settings()
    _require_favorites_enabled(settings)
    with db.get_connection(settings.db_path) as conn:
        return _enrich_favorites_list(conn, settings)


@app.post("/favorites")
def create_favorite(payload: FavoriteCreate) -> dict[str, Any]:
    settings = _settings()
    _require_favorites_enabled(settings)
    barcode = payload.barcode
    if payload.source == "off" and not barcode:
        barcode = payload.id
    with db.get_connection(settings.db_path) as conn:
        favorite = db.create_favorite(
            conn,
            payload.display_name.strip(),
            payload.source,
            payload.id,
            barcode=barcode,
            brand=payload.brand,
            default_amount_g=payload.default_amount_g,
        )
        return favorites.enrich_favorite(
            favorite,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )


@app.get("/favorites/{favorite_id}")
def get_favorite(favorite_id: int) -> dict[str, Any]:
    settings = _settings()
    _require_favorites_enabled(settings)
    with db.get_connection(settings.db_path) as conn:
        favorite = db.get_favorite(conn, favorite_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
        return favorites.enrich_favorite(
            favorite,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )


@app.patch("/favorites/{favorite_id}")
def update_favorite(favorite_id: int, payload: FavoriteUpdate) -> dict[str, Any]:
    settings = _settings()
    _require_favorites_enabled(settings)
    with db.get_connection(settings.db_path) as conn:
        favorite = db.update_favorite(
            conn,
            favorite_id,
            display_name=payload.display_name.strip() if payload.display_name else None,
            default_amount_g=payload.default_amount_g,
        )
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
        return favorites.enrich_favorite(
            favorite,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )


@app.delete("/favorites/{favorite_id}")
def remove_favorite(favorite_id: int) -> dict[str, str]:
    settings = _settings()
    _require_favorites_enabled(settings)
    with db.get_connection(settings.db_path) as conn:
        favorite = db.get_favorite(conn, favorite_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
        if favorite.get("image_path"):
            local = favorites.local_image_file(
                settings.data_dir, str(favorite["image_path"])
            )
            if local:
                local.unlink(missing_ok=True)
        if not db.delete_favorite(conn, favorite_id):
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
    return {"status": "deleted"}


@app.delete("/favorites/by-source/{source}/{item_id}")
def remove_favorite_by_source(source: str, item_id: str) -> dict[str, str]:
    settings = _settings()
    _require_favorites_enabled(settings)
    if source not in ("bls", "off", "custom"):
        raise HTTPException(status_code=400, detail="Ungültige Quelle")
    with db.get_connection(settings.db_path) as conn:
        favorite = db.get_favorite_by_source(conn, source, item_id)
        if favorite and favorite.get("image_path"):
            local = favorites.local_image_file(
                settings.data_dir, str(favorite["image_path"])
            )
            if local:
                local.unlink(missing_ok=True)
        if not db.delete_favorite_by_source(conn, source, item_id):
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
    return {"status": "deleted"}


@app.post("/favorites/{favorite_id}/image")
async def upload_favorite_image(
    favorite_id: int, file: UploadFile = File(...)
) -> dict[str, Any]:
    settings = _settings()
    _require_favorites_enabled(settings)
    content_type = (file.content_type or "").lower()
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Nur JPEG, PNG oder WebP erlaubt")
    suffix = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[content_type]
    data = await file.read()
    if not data or len(data) > 2_000_000:
        raise HTTPException(status_code=400, detail="Bild zu groß (max. 2 MB)")

    media_dir = favorites.favorites_media_dir(settings.data_dir)
    relative_path = f"favorites/{favorite_id}{suffix}"
    target = media_dir / f"{favorite_id}{suffix}"
    target.write_bytes(data)

    with db.get_connection(settings.db_path) as conn:
        favorite = db.update_favorite(
            conn,
            favorite_id,
            image_path=relative_path,
            clear_image_url=True,
        )
        if not favorite:
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
        return favorites.enrich_favorite(
            favorite,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )


@app.get("/favorites/{favorite_id}/image")
def favorite_image(favorite_id: int) -> FileResponse | RedirectResponse:
    settings = _settings()
    _require_favorites_enabled(settings)
    with db.get_connection(settings.db_path) as conn:
        favorite = db.get_favorite(conn, favorite_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorit nicht gefunden")
        local = favorites.local_image_file(settings.data_dir, favorite.get("image_path"))
        if local:
            media_type = "image/jpeg"
            if local.suffix == ".png":
                media_type = "image/png"
            elif local.suffix == ".webp":
                media_type = "image/webp"
            return FileResponse(local, media_type=media_type)
        enriched = favorites.enrich_favorite(
            favorite,
            data_dir=settings.data_dir,
            enable_network=settings.enable_open_food_facts,
            conn=conn,
        )
        image_url = enriched.get("resolved_image")
        if image_url and str(image_url).startswith("http"):
            return RedirectResponse(image_url)
    raise HTTPException(status_code=404, detail="Kein Bild verfügbar")


@app.post("/calculate/portion", response_model=CalculationResult)
def calculate_portion(request: PortionRequest) -> CalculationResult:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        try:
            result = calculator.calculate_portion(
                conn,
                request.source,
                request.id,
                request.amount_g,
                settings.language,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CalculationResult(
        source=result["source"],
        id=result["id"],
        name=result["name"],
        amount_g=result["amount_g"],
        nutrients=result["nutrients"],
        diabetes=_diabetes_model(result["diabetes"]),
        nutriscore=result.get("nutriscore"),
        nova_group=result.get("nova_group"),
        ecoscore=result.get("ecoscore"),
    )


@app.post("/calculate/recipe", response_model=CalculationResult)
def calculate_recipe(request: RecipeRequest) -> CalculationResult:
    settings = _settings()
    ingredients = [item.model_dump() for item in request.ingredients]
    with db.get_connection(settings.db_path) as conn:
        result = calculator.calculate_recipe(
            conn, ingredients, request.servings, settings.language
        )
    return CalculationResult(
        servings=result["servings"],
        nutrients=result["nutrients"],
        diabetes=_diabetes_model(result["diabetes"]),
        ingredients=result["ingredients"],
    )


@app.get("/custom-foods")
def list_custom_foods() -> list[dict[str, Any]]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        return db.list_custom_foods(conn)


@app.post("/custom-foods")
def create_custom_food(payload: CustomFoodCreate) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        food_id = db.create_custom_food(conn, payload.name, payload.notes, payload.nutrients)
        food = db.get_custom_food(conn, food_id)
    return food or {"id": food_id}


@app.get("/custom-foods/{food_id}")
def get_custom_food(food_id: int) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        food = db.get_custom_food(conn, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Custom food not found")
    return food


@app.put("/custom-foods/{food_id}")
def update_custom_food(food_id: int, payload: CustomFoodUpdate) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        updated = db.update_custom_food(
            conn, food_id, payload.name, payload.notes, payload.nutrients
        )
        food = db.get_custom_food(conn, food_id)
    if not updated and not food:
        raise HTTPException(status_code=404, detail="Custom food not found")
    return food or {"id": food_id}


@app.delete("/custom-foods/{food_id}")
def delete_custom_food(food_id: int) -> dict[str, str]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        if not db.delete_custom_food(conn, food_id):
            raise HTTPException(status_code=404, detail="Custom food not found")
    return {"status": "deleted"}


@app.get("/custom-recipes")
def list_custom_recipes() -> list[dict[str, Any]]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        return db.list_custom_recipes(conn)


@app.post("/custom-recipes")
def create_custom_recipe(payload: CustomRecipeCreate) -> dict[str, Any]:
    settings = _settings()
    ingredients = [item.model_dump() for item in payload.ingredients]
    with db.get_connection(settings.db_path) as conn:
        recipe_id = db.create_custom_recipe(
            conn, payload.name, payload.servings, ingredients
        )
        recipe = db.get_custom_recipe(conn, recipe_id)
    return recipe or {"id": recipe_id}


@app.get("/custom-recipes/{recipe_id}")
def get_custom_recipe(recipe_id: int) -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        recipe = db.get_custom_recipe(conn, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.delete("/custom-recipes/{recipe_id}")
def delete_custom_recipe(recipe_id: int) -> dict[str, str]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        if not db.delete_custom_recipe(conn, recipe_id):
            raise HTTPException(status_code=404, detail="Recipe not found")
    return {"status": "deleted"}
