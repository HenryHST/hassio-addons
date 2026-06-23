"""Runtime configuration from environment and addon options."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path
    downloads_dir: Path
    auto_update: bool
    update_interval_days: int
    language: str
    enable_open_food_facts: bool
    off_cache_ttl_days: int
    off_search_cache_ttl_days: int
    search_layout: str
    search_recents_enabled: bool
    todo_list_enabled: bool
    todo_list_entity_id: str
    map_enabled: bool
    map_radius_km: int
    bls_version: str
    addon_version: str


def _options_path(data_dir: Path) -> Path:
    return data_dir / "options.json"


def _read_option_bool(
    data_dir: Path, option_name: str, env_name: str, default: bool
) -> bool:
    config_path = _options_path(data_dir)
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if option_name in data and data[option_name] is not None:
                value = data[option_name]
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    lowered = value.lower()
                    if lowered in ("true", "false"):
                        return lowered == "true"
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    env_default = "true" if default else "false"
    return os.environ.get(env_name, env_default).lower() == "true"


def _read_option_int(
    data_dir: Path, option_name: str, env_name: str, default: int, minimum: int, maximum: int
) -> int:
    config_path = _options_path(data_dir)
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            value = data.get(option_name)
            if value is not None:
                parsed = int(value)
                return max(minimum, min(maximum, parsed))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
    try:
        parsed = int(os.environ.get(env_name, str(default)))
    except ValueError:
        parsed = default
    return max(minimum, min(maximum, parsed))


def get_settings() -> Settings:
    data_dir = Path(os.environ.get("BLS_DATA_DIR", "/data"))
    layout = os.environ.get("BLS_SEARCH_LAYOUT", "stacked")
    if layout not in ("stacked", "side_by_side"):
        layout = "stacked"
    return Settings(
        data_dir=data_dir,
        db_path=data_dir / "bls.sqlite",
        downloads_dir=data_dir / "downloads",
        auto_update=os.environ.get("BLS_AUTO_UPDATE", "true").lower() == "true",
        update_interval_days=int(os.environ.get("BLS_UPDATE_INTERVAL_DAYS", "30")),
        language=os.environ.get("BLS_LANGUAGE", "de"),
        enable_open_food_facts=os.environ.get("BLS_ENABLE_OFF", "true").lower()
        == "true",
        off_cache_ttl_days=int(os.environ.get("BLS_OFF_CACHE_TTL_DAYS", "90")),
        off_search_cache_ttl_days=int(
            os.environ.get("BLS_OFF_SEARCH_CACHE_TTL_DAYS", "7")
        ),
        search_layout=layout,
        search_recents_enabled=_read_option_bool(
            data_dir, "search_recents_enabled", "BLS_SEARCH_RECENTS_ENABLED", True
        ),
        todo_list_enabled=_read_option_bool(
            data_dir, "todo_list_enabled", "BLS_TODO_LIST_ENABLED", False
        ),
        todo_list_entity_id=os.environ.get(
            "BLS_TODO_LIST_ENTITY_ID", "todo.shopping_list"
        ),
        map_enabled=_read_option_bool(
            data_dir, "map_enabled", "BLS_MAP_ENABLED", False
        ),
        map_radius_km=_read_option_int(
            data_dir, "map_radius_km", "BLS_MAP_RADIUS_KM", 20, 1, 50
        ),
        bls_version=os.environ.get("BLS_VERSION", "4.0"),
        addon_version=os.environ.get("ADDON_VERSION", "1.0.0"),
    )
