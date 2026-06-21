"""Runtime data for BLS Nährwertdatenbank."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import BlsNutritionClient


@dataclass
class BlsRuntimeData:
    """Per-config-entry runtime state."""

    client: BlsNutritionClient
    coordinator: DataUpdateCoordinator
    last_search: list[dict[str, Any]] = field(default_factory=list)
    last_search_query: str = ""
    last_calculation: dict[str, Any] = field(default_factory=dict)
    last_calculation_type: str = ""

    def set_search(self, query: str, results: list[dict[str, Any]]) -> None:
        self.last_search_query = query
        self.last_search = results

    def set_calculation(self, calc_type: str, result: dict[str, Any]) -> None:
        self.last_calculation_type = calc_type
        self.last_calculation = result
