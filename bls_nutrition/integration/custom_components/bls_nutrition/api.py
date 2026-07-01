"""API client for the BLS Nährwertdatenbank add-on."""

from __future__ import annotations

from typing import Any

import aiohttp


class BlsNutritionApiError(Exception):
    """Raised when the add-on API returns an error."""


class BlsNutritionClient:
    """HTTP client for the add-on REST API."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        self._base_url = f"http://{host}:{port}"
        self._session = session

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        async with self._session.request(method, url, params=params, json=json) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise BlsNutritionApiError(f"HTTP {resp.status}: {text}")
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.text()

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/health")

    async def search_food(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self._request(
            "GET", "/foods/search", params={"q": query, "limit": limit}
        )

    async def lookup_barcode(self, barcode: str) -> dict[str, Any]:
        return await self._request("GET", f"/foods/barcode/{barcode}")

    async def calculate_portion(
        self, source: str, item_id: str, amount_g: float
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/calculate/portion",
            json={"source": source, "id": item_id, "amount_g": amount_g},
        )

    async def calculate_recipe(
        self, ingredients: list[dict[str, Any]], servings: int = 1
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/calculate/recipe",
            json={"ingredients": ingredients, "servings": servings},
        )

    async def save_recipe(
        self, name: str, ingredients: list[dict[str, Any]], servings: int = 1
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/custom-recipes",
            json={"name": name, "ingredients": ingredients, "servings": servings},
        )

    async def save_custom_food(
        self, name: str, nutrients: dict[str, float], notes: str | None = None
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/custom-foods",
            json={"name": name, "nutrients": nutrients, "notes": notes},
        )

    async def list_favorites(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/favorites")

    async def add_favorite(
        self,
        display_name: str,
        source: str,
        item_id: str,
        *,
        barcode: str | None = None,
        brand: str | None = None,
        default_amount_g: float = 100.0,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/favorites",
            json={
                "display_name": display_name,
                "source": source,
                "id": item_id,
                "barcode": barcode,
                "brand": brand,
                "default_amount_g": default_amount_g,
            },
        )

    async def remove_favorite(self, favorite_id: int) -> dict[str, Any]:
        return await self._request("DELETE", f"/favorites/{favorite_id}")
