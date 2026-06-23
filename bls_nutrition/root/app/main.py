"""FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
import html as html_module
from typing import Any, AsyncIterator

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import calculator, db, home_assistant, open_food_facts
from app.models import (
    CalculationResult,
    CustomFoodCreate,
    CustomFoodUpdate,
    CustomRecipeCreate,
    DiabetesUnits,
    PortionRequest,
    RecipeRequest,
    TodoListItemRequest,
)
from app.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="BLS Nährwertdatenbank",
    version="1.6.3",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _settings() -> Settings:
    return get_settings()


def _diabetes_model(data: dict[str, Any]) -> DiabetesUnits:
    return DiabetesUnits(**data)


@app.get("/health")
def health() -> dict[str, Any]:
    settings = _settings()
    with db.get_connection(settings.db_path) as conn:
        return {
            "status": "ok",
            "addon_version": settings.addon_version,
            "bls_version": db.get_meta(conn, "bls_version") or settings.bls_version,
            "imported_at": db.get_meta(conn, "imported_at"),
            "food_count": db.food_count(conn),
            "open_food_facts_enabled": settings.enable_open_food_facts,
            "search_layout": settings.search_layout,
            "search_recents_enabled": settings.search_recents_enabled,
            "todo_list_enabled": settings.todo_list_enabled,
            "todo_list_entity_id": settings.todo_list_entity_id,
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
