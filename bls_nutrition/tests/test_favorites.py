"""Tests for favorites persistence."""

from __future__ import annotations

from pathlib import Path

from app import db


def test_create_update_delete_favorite(tmp_path: Path) -> None:
    db_path = tmp_path / "test.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        favorite = db.create_favorite(
            conn,
            "Apfel",
            "bls",
            "F110000",
            default_amount_g=120,
        )
        assert favorite["display_name"] == "Apfel"
        assert favorite["default_amount_g"] == 120.0
        assert db.favorites_count(conn) == 1

        updated = db.update_favorite(
            conn,
            int(favorite["id"]),
            display_name="Bio-Apfel",
            default_amount_g=150,
        )
        assert updated is not None
        assert updated["display_name"] == "Bio-Apfel"
        assert updated["default_amount_g"] == 150.0

        assert db.get_favorite_by_source(conn, "bls", "F110000") is not None
        assert db.delete_favorite(conn, int(favorite["id"]))
        assert db.favorites_count(conn) == 0


def test_create_favorite_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "fav.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        first = db.create_favorite(conn, "Banane", "bls", "X001")
        second = db.create_favorite(conn, "Banane", "bls", "X001")
        assert first["id"] == second["id"]
        assert db.favorites_count(conn) == 1
