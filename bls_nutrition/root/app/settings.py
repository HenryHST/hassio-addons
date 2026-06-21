"""Runtime configuration from environment and addon options."""

from __future__ import annotations

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
    bls_version: str
    addon_version: str


def get_settings() -> Settings:
    data_dir = Path(os.environ.get("BLS_DATA_DIR", "/data"))
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
        bls_version=os.environ.get("BLS_VERSION", "4.0"),
        addon_version=os.environ.get("ADDON_VERSION", "1.0.0"),
    )
