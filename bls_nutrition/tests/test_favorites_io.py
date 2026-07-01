"""Tests for favorites import/export."""

from __future__ import annotations

import json
from pathlib import Path

from app import db, favorites_io


def test_export_import_json_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "fav.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        db.create_favorite(conn, "Apfel", "bls", "F110000", default_amount_g=120)
        items = db.list_favorites(conn)
        exported = favorites_io.export_json_bytes(items, "1.8.4")
        parsed = favorites_io.parse_import_bytes(exported, "favorites.json")
        assert len(parsed) == 1
        assert parsed[0]["display_name"] == "Apfel"
        assert parsed[0]["source_id"] == "F110000"


def test_export_import_csv_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "fav.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        db.create_favorite(conn, "Banane", "off", "4001234567890", barcode="4001234567890")
        items = db.list_favorites(conn)
        exported = favorites_io.export_csv_bytes(items)
        parsed = favorites_io.parse_import_bytes(exported, "favorites.csv")
        assert len(parsed) == 1
        assert parsed[0]["source"] == "off"
        assert parsed[0]["barcode"] == "4001234567890"


def test_import_favorites_merge_skips_duplicates(tmp_path: Path) -> None:
    db_path = tmp_path / "fav.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        db.create_favorite(conn, "Apfel", "bls", "F110000")
        payload = favorites_io.export_json_payload(
            [
                {
                    "display_name": "Apfel",
                    "source": "bls",
                    "source_id": "F110000",
                    "barcode": None,
                    "brand": None,
                    "default_amount_g": 100,
                    "image_url": None,
                    "sort_order": 0,
                },
                {
                    "display_name": "Birne",
                    "source": "bls",
                    "source_id": "F120000",
                    "barcode": None,
                    "brand": None,
                    "default_amount_g": 100,
                    "image_url": None,
                    "sort_order": 1,
                },
            ],
            "1.8.4",
        )
        items = favorites_io.parse_import_bytes(
            json.dumps(payload).encode("utf-8"), "favorites.json"
        )
        result = db.import_favorites(conn, items, "merge")
        assert result["imported"] == 1
        assert result["skipped"] == 1
        assert db.favorites_count(conn) == 2


def test_import_favorites_replace_clears_existing(tmp_path: Path) -> None:
    db_path = tmp_path / "fav.duckdb"
    with db.get_connection(db_path) as conn:
        db.init_schema(conn)
        db.create_favorite(conn, "Alt", "bls", "OLD001")
        items = favorites_io.parse_import_bytes(
            json.dumps(
                [
                    {
                        "display_name": "Neu",
                        "source": "bls",
                        "source_id": "NEW001",
                        "default_amount_g": 80,
                    }
                ]
            ).encode("utf-8"),
            "favorites.json",
        )
        result = db.import_favorites(conn, items, "replace")
        assert result["imported"] == 1
        assert db.favorites_count(conn) == 1
        favorite = db.get_favorite_by_source(conn, "bls", "NEW001")
        assert favorite is not None
        assert favorite["display_name"] == "Neu"


def test_parse_import_rejects_invalid_source() -> None:
    try:
        favorites_io.parse_import_bytes(
            json.dumps(
                [{"display_name": "X", "source": "invalid", "source_id": "1"}]
            ).encode("utf-8"),
            "favorites.json",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Ungültige Quelle" in str(exc)
