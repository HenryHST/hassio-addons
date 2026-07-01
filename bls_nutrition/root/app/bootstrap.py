"""Database bootstrap and BLS import orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import db, download, import_bls
from app.settings import Settings, get_settings


def _version_info_path(data_dir: Path) -> Path:
    return data_dir / "bls_version.json"


def _needs_update(info_path: Path, interval_days: int) -> bool:
    if not info_path.exists():
        return True
    try:
        payload = json.loads(info_path.read_text(encoding="utf-8"))
        imported_at = datetime.fromisoformat(payload["imported_at"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return True
    return imported_at < datetime.now(timezone.utc) - timedelta(days=interval_days)


def _import_required(settings: Settings, count: int) -> bool:
    if count == 0:
        return True
    if not settings.auto_update:
        return False
    return _needs_update(_version_info_path(settings.data_dir), settings.update_interval_days)


def prepare_database() -> bool:
    """Fast startup: migrate, schema, purge. Returns True if BLS import should run."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)

    db.migrate_from_sqlite(settings.legacy_sqlite_path, settings.db_path)

    with db.get_connection(settings.db_path) as conn:
        db.init_schema(conn)
        db.purge_expired_cache(
            conn,
            settings.off_cache_ttl_days,
            settings.off_search_cache_ttl_days,
        )
        count = db.food_count(conn)

        if not _import_required(settings, count):
            db.set_database_status(conn, "ready")
            print(f"[bls-bootstrap] Database ready ({count} foods)")
            return False

        db.set_database_status(conn, "importing")

    print("[bls-bootstrap] BLS import scheduled in background")
    return True


def run_bls_import() -> None:
    """Download and import BLS data. Intended for a background thread."""
    settings = get_settings()
    print("[bls-bootstrap] Importing BLS 4.0 data...")

    try:
        zip_path = download.download_bls_archive(settings.downloads_dir)
        data_path, components_path = download.extract_bls_files(
            zip_path, settings.downloads_dir
        )

        with db.get_connection(settings.db_path) as conn:
            conn.execute("DELETE FROM food_nutrients")
            conn.execute("DELETE FROM foods")
            conn.execute("DELETE FROM nutrients")
            db.init_schema(conn)
            import_bls.import_components(conn, components_path)
            imported = import_bls.import_data(conn, data_path)
            db.set_meta(conn, "bls_version", settings.bls_version)
            db.set_meta(conn, "imported_at", datetime.now(timezone.utc).isoformat())
            db.set_meta(conn, "food_count", str(imported))
            db.set_database_status(conn, "ready")

        info = {
            "bls_version": settings.bls_version,
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "food_count": imported,
            "data_file": str(data_path),
            "database_engine": "duckdb",
        }
        _version_info_path(settings.data_dir).write_text(
            json.dumps(info, indent=2), encoding="utf-8"
        )
        print(f"[bls-bootstrap] Imported {imported} foods")
    except Exception as exc:
        print(f"[bls-bootstrap] Import failed: {exc}")
        with db.get_connection(settings.db_path) as conn:
            db.set_database_status(conn, "error")
        raise


def ensure_database() -> None:
    """CLI helper: prepare synchronously and import in foreground."""
    if prepare_database():
        run_bls_import()


if __name__ == "__main__":
    ensure_database()
