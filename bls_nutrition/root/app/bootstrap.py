"""Database bootstrap and BLS import orchestration."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import db, download, import_bls
from app.settings import get_settings

DEBUG_LOG_PATH = Path("/Users/henry/Projects/hassio-addons/.cursor/debug-92f7bb.log")


def _debug_log(
    hypothesis_id: str, location: str, message: str, data: dict[str, object] | None = None
) -> None:
    payload = {
        "sessionId": "92f7bb",
        "runId": "run1",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except OSError:
        pass


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


def ensure_database() -> None:
    started = time.monotonic()
    settings = get_settings()
    print(f"[bls-debug] ensure_database enter t=0.0s db={settings.db_path}")
    # #region agent log
    _debug_log(
        "H1",
        "bootstrap.py:52",
        "ensure_database_enter",
        {"db_path": str(settings.db_path), "legacy_sqlite_path": str(settings.legacy_sqlite_path)},
    )
    # #endregion
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)

    # #region agent log
    _debug_log("H1", "bootstrap.py:62", "migrate_from_sqlite_start")
    # #endregion
    db.migrate_from_sqlite(settings.legacy_sqlite_path, settings.db_path)
    print(f"[bls-debug] migrate_from_sqlite done t={time.monotonic()-started:.1f}s")
    # #region agent log
    _debug_log("H1", "bootstrap.py:65", "migrate_from_sqlite_done")
    # #endregion

    with db.get_connection(settings.db_path) as conn:
        db.init_schema(conn)
        db.purge_expired_cache(
            conn,
            settings.off_cache_ttl_days,
            settings.off_search_cache_ttl_days,
        )
        count = db.food_count(conn)
        print(f"[bls-debug] init_schema+purge done t={time.monotonic()-started:.1f}s count={count}")
        # #region agent log
        _debug_log("H2", "bootstrap.py:75", "database_count_after_init", {"food_count": count})
        # #endregion

    should_import = count == 0
    if settings.auto_update and not should_import:
        should_import = _needs_update(
            _version_info_path(settings.data_dir), settings.update_interval_days
        )

    if not should_import:
        with db.get_connection(settings.db_path) as conn:
            db.set_database_status(conn, "ready")
        print(f"[bls-bootstrap] Database ready ({count} foods)")
        print(f"[bls-debug] ensure_database exit t={time.monotonic()-started:.1f}s path=no_import")
        return

    print("[bls-bootstrap] Importing BLS 4.0 data...")
    print(f"[bls-debug] import path selected t={time.monotonic()-started:.1f}s")
    # #region agent log
    _debug_log("H3", "bootstrap.py:90", "import_required", {"reason": "count_zero_or_update_due"})
    # #endregion
    with db.get_connection(settings.db_path) as conn:
        db.set_database_status(conn, "importing")

    zip_path = download.download_bls_archive(settings.downloads_dir)
    print(f"[bls-debug] download_bls_archive done t={time.monotonic()-started:.1f}s zip={zip_path}")
    data_path, components_path = download.extract_bls_files(
        zip_path, settings.downloads_dir
    )
    print(f"[bls-debug] extract_bls_files done t={time.monotonic()-started:.1f}s")

    with db.get_connection(settings.db_path) as conn:
        conn.execute("DELETE FROM food_nutrients")
        conn.execute("DELETE FROM foods")
        conn.execute("DELETE FROM nutrients")
        db.init_schema(conn)
        import_bls.import_components(conn, components_path)
        imported = import_bls.import_data(conn, data_path)
        print(f"[bls-debug] import_data done t={time.monotonic()-started:.1f}s imported={imported}")
        # #region agent log
        _debug_log("H4", "bootstrap.py:108", "import_data_done", {"imported": imported})
        # #endregion
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
    print(f"[bls-debug] ensure_database exit t={time.monotonic()-started:.1f}s path=import")


if __name__ == "__main__":
    ensure_database()
