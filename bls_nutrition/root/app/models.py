"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SourceType = Literal["bls", "off", "custom"]


class Ingredient(BaseModel):
    source: SourceType
    id: str
    amount_g: float = Field(gt=0)


class PortionRequest(BaseModel):
    source: SourceType
    id: str
    amount_g: float = Field(gt=0)


class RecipeRequest(BaseModel):
    ingredients: list[Ingredient]
    servings: int = Field(default=1, ge=1)


class CustomFoodCreate(BaseModel):
    name: str = Field(min_length=1)
    notes: str | None = None
    nutrients: dict[str, float] = Field(default_factory=dict)


class CustomFoodUpdate(BaseModel):
    name: str | None = None
    notes: str | None = None
    nutrients: dict[str, float] | None = None


class CustomRecipeCreate(BaseModel):
    name: str = Field(min_length=1)
    servings: int = Field(default=1, ge=1)
    ingredients: list[Ingredient] = Field(default_factory=list)


class TodoListItemRequest(BaseModel):
    name: str = Field(min_length=1)
    barcode: str | None = None
    brand: str | None = None


class DiabetesUnits(BaseModel):
    g_kh: float | None = None
    be: float | None = None
    ke: float | None = None
    fpe: float | None = None


class NutrientResult(BaseModel):
    code: str
    name_de: str | None = None
    name_en: str | None = None
    unit: str | None = None
    value: float | None = None


class CalculationResult(BaseModel):
    source: SourceType | None = None
    id: str | None = None
    name: str | None = None
    amount_g: float | None = None
    servings: int | None = None
    nutrients: dict[str, float | None]
    diabetes: DiabetesUnits
    ingredients: list[dict[str, Any]] | None = None
    nutriscore: str | None = None
    nova_group: int | None = None
    ecoscore: str | None = None
