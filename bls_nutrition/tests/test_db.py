"""DuckDB schema and query smoke tests."""

from __future__ import annotations

from pathlib import Path

from app import db


def test_init_schema_and_search(tmp_path: Path) -> None:
    db_path = tmp_path / "test.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        conn.execute(
            "INSERT INTO foods(bls_code, name_de, name_en) VALUES (?, ?, ?)",
            ["T001", "Apfel", "Apple"],
        )
        conn.execute(
            "INSERT INTO foods(bls_code, name_de, name_en) VALUES (?, ?, ?)",
            ["T002", "Birne", "Pear"],
        )
        db.set_meta(conn, "imported_at", "2026-06-23T12:00:00+00:00")
        db.set_database_status(conn, "ready")

        assert db.food_count(conn) == 2
        assert db.get_database_status(conn) == "ready"
        assert db.get_meta(conn, "database_engine") == "duckdb"

        results = db.search_foods(conn, "Apfel", limit=10)
        assert len(results) == 1
        assert results[0]["id"] == "T001"


def test_purge_expired_cache(tmp_path: Path) -> None:
    db_path = tmp_path / "cache.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        conn.execute(
            """
            INSERT INTO off_products(barcode, name, brand, nutrients_json, fetched_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ["123", "Test", "Brand", "{}", "2020-01-01T00:00:00+00:00"],
        )
        conn.execute(
            """
            INSERT INTO off_search_cache(cache_key, results_json, fetched_at)
            VALUES (?, ?, ?)
            """,
            ["q:apfel", "[]", "2020-01-01T00:00:00+00:00"],
        )
        db.purge_expired_cache(conn, off_cache_ttl_days=90, off_search_cache_ttl_days=7)
        assert db.off_products_count(conn) == 0
