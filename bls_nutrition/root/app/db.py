"""SQLite database schema and queries."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterator


KEY_NUTRIENTS = ("ENERCC", "ENERCJ", "CHO", "FAT", "PROT625", "FIBT", "NACL", "WATER")


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS foods (
            bls_code TEXT PRIMARY KEY,
            name_de TEXT NOT NULL,
            name_en TEXT
        );

        CREATE TABLE IF NOT EXISTS nutrients (
            code TEXT PRIMARY KEY,
            name_de TEXT,
            name_en TEXT,
            unit TEXT,
            nutrient_group TEXT
        );

        CREATE TABLE IF NOT EXISTS food_nutrients (
            bls_code TEXT NOT NULL,
            nutrient_code TEXT NOT NULL,
            value REAL,
            provenance TEXT,
            reference TEXT,
            PRIMARY KEY (bls_code, nutrient_code),
            FOREIGN KEY (bls_code) REFERENCES foods(bls_code),
            FOREIGN KEY (nutrient_code) REFERENCES nutrients(code)
        );

        CREATE TABLE IF NOT EXISTS custom_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS custom_food_nutrients (
            custom_food_id INTEGER NOT NULL,
            nutrient_code TEXT NOT NULL,
            value REAL,
            PRIMARY KEY (custom_food_id, nutrient_code),
            FOREIGN KEY (custom_food_id) REFERENCES custom_foods(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS custom_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            servings INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            amount_g REAL NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES custom_recipes(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS off_products (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            brand TEXT,
            nutrients_json TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );
        """
    )


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def search_foods(
    conn: sqlite3.Connection, query: str, limit: int = 20, language: str = "de"
) -> list[dict[str, Any]]:
    pattern = f"%{query.strip()}%"
    if not pattern.strip("%"):
        return []
    rows = conn.execute(
        """
        SELECT bls_code, name_de, name_en
        FROM foods
        WHERE name_de LIKE ? OR name_en LIKE ? OR bls_code LIKE ?
        ORDER BY
            CASE
                WHEN name_de LIKE ? THEN 0
                WHEN name_en LIKE ? THEN 1
                ELSE 2
            END,
            name_de
        LIMIT ?
        """,
        (pattern, pattern, pattern, f"{query.strip()}%", f"{query.strip()}%", limit),
    ).fetchall()
    return [
        {
            "source": "bls",
            "id": row["bls_code"],
            "name": row["name_de"] if language == "de" else (row["name_en"] or row["name_de"]),
            "name_de": row["name_de"],
            "name_en": row["name_en"],
        }
        for row in rows
    ]


def get_food_name(conn: sqlite3.Connection, bls_code: str, language: str = "de") -> str | None:
    row = conn.execute(
        "SELECT name_de, name_en FROM foods WHERE bls_code = ?", (bls_code,)
    ).fetchone()
    if not row:
        return None
    return row["name_de"] if language == "de" else (row["name_en"] or row["name_de"])


def get_nutrients_per_100g(
    conn: sqlite3.Connection, source: str, item_id: str
) -> dict[str, float | None]:
    if source == "bls":
        rows = conn.execute(
            """
            SELECT fn.nutrient_code AS code, fn.value
            FROM food_nutrients fn
            WHERE fn.bls_code = ?
            """,
            (item_id,),
        ).fetchall()
        return {row["code"]: row["value"] for row in rows}

    if source == "custom":
        rows = conn.execute(
            """
            SELECT nutrient_code AS code, value
            FROM custom_food_nutrients
            WHERE custom_food_id = ?
            """,
            (int(item_id),),
        ).fetchall()
        return {row["code"]: row["value"] for row in rows}

    if source == "off":
        row = conn.execute(
            "SELECT nutrients_json FROM off_products WHERE barcode = ?", (item_id,)
        ).fetchone()
        if not row:
            return {}
        data = json.loads(row["nutrients_json"])
        return {k: v for k, v in data.items() if isinstance(v, (int, float))}

    return {}


def get_key_nutrients(nutrients: dict[str, float | None]) -> dict[str, float | None]:
    aliases = {
        "ENERCC": ("ENERCC", "energy_kcal"),
        "ENERCJ": ("ENERCJ", "energy_kj"),
        "CHO": ("CHO", "carbohydrates"),
        "FAT": ("FAT", "fat"),
        "PROT625": ("PROT625", "proteins"),
        "FIBT": ("FIBT", "fiber"),
        "NACL": ("NACL", "salt"),
        "WATER": ("WATER", "water"),
    }
    result: dict[str, float | None] = {}
    for code, keys in aliases.items():
        for key in keys:
            if key in nutrients and nutrients[key] is not None:
                result[code] = nutrients[key]
                break
        else:
            result[code] = None
    return result


def save_off_product(
    conn: sqlite3.Connection,
    barcode: str,
    name: str | None,
    brand: str | None,
    nutrients: dict[str, float | None],
) -> None:
    conn.execute(
        """
        INSERT INTO off_products(barcode, name, brand, nutrients_json, fetched_at)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name = excluded.name,
            brand = excluded.brand,
            nutrients_json = excluded.nutrients_json,
            fetched_at = excluded.fetched_at
        """,
        (
            barcode,
            name,
            brand,
            json.dumps(nutrients),
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def get_off_product(conn: sqlite3.Connection, barcode: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT barcode, name, brand, nutrients_json, fetched_at FROM off_products WHERE barcode = ?",
        (barcode,),
    ).fetchone()
    if not row:
        return None
    return {
        "source": "off",
        "id": row["barcode"],
        "name": row["name"],
        "brand": row["brand"],
        "nutrients": json.loads(row["nutrients_json"]),
        "fetched_at": row["fetched_at"],
    }


def list_custom_foods(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, name, notes, created_at FROM custom_foods ORDER BY name"
    ).fetchall()
    return [dict(row) for row in rows]


def get_custom_food(conn: sqlite3.Connection, food_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, name, notes, created_at FROM custom_foods WHERE id = ?",
        (food_id,),
    ).fetchone()
    if not row:
        return None
    nutrients = get_nutrients_per_100g(conn, "custom", str(food_id))
    return {**dict(row), "nutrients": nutrients}


def create_custom_food(
    conn: sqlite3.Connection, name: str, notes: str | None, nutrients: dict[str, float]
) -> int:
    cur = conn.execute(
        "INSERT INTO custom_foods(name, notes, created_at) VALUES(?, ?, ?)",
        (name, notes, datetime.now(timezone.utc).isoformat()),
    )
    food_id = int(cur.lastrowid)
    for code, value in nutrients.items():
        conn.execute(
            "INSERT INTO custom_food_nutrients(custom_food_id, nutrient_code, value) VALUES(?, ?, ?)",
            (food_id, code, value),
        )
    return food_id


def update_custom_food(
    conn: sqlite3.Connection,
    food_id: int,
    name: str | None,
    notes: str | None,
    nutrients: dict[str, float] | None,
) -> bool:
    row = conn.execute("SELECT id FROM custom_foods WHERE id = ?", (food_id,)).fetchone()
    if not row:
        return False
    if name is not None:
        conn.execute("UPDATE custom_foods SET name = ? WHERE id = ?", (name, food_id))
    if notes is not None:
        conn.execute("UPDATE custom_foods SET notes = ? WHERE id = ?", (notes, food_id))
    if nutrients is not None:
        conn.execute(
            "DELETE FROM custom_food_nutrients WHERE custom_food_id = ?", (food_id,)
        )
        for code, value in nutrients.items():
            conn.execute(
                "INSERT INTO custom_food_nutrients(custom_food_id, nutrient_code, value) VALUES(?, ?, ?)",
                (food_id, code, value),
            )
    return True


def delete_custom_food(conn: sqlite3.Connection, food_id: int) -> bool:
    cur = conn.execute("DELETE FROM custom_foods WHERE id = ?", (food_id,))
    return cur.rowcount > 0


def list_custom_recipes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, name, servings, created_at FROM custom_recipes ORDER BY name"
    ).fetchall()
    return [dict(row) for row in rows]


def get_custom_recipe(conn: sqlite3.Connection, recipe_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, name, servings, created_at FROM custom_recipes WHERE id = ?",
        (recipe_id,),
    ).fetchone()
    if not row:
        return None
    ingredients = conn.execute(
        """
        SELECT source_type AS source, source_id AS id, amount_g
        FROM recipe_ingredients WHERE recipe_id = ?
        """,
        (recipe_id,),
    ).fetchall()
    return {**dict(row), "ingredients": [dict(i) for i in ingredients]}


def create_custom_recipe(
    conn: sqlite3.Connection,
    name: str,
    servings: int,
    ingredients: list[dict[str, Any]],
) -> int:
    cur = conn.execute(
        "INSERT INTO custom_recipes(name, servings, created_at) VALUES(?, ?, ?)",
        (name, servings, datetime.now(timezone.utc).isoformat()),
    )
    recipe_id = int(cur.lastrowid)
    for ingredient in ingredients:
        conn.execute(
            """
            INSERT INTO recipe_ingredients(recipe_id, source_type, source_id, amount_g)
            VALUES(?, ?, ?, ?)
            """,
            (
                recipe_id,
                ingredient["source"],
                ingredient["id"],
                ingredient["amount_g"],
            ),
        )
    return recipe_id


def delete_custom_recipe(conn: sqlite3.Connection, recipe_id: int) -> bool:
    conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    cur = conn.execute("DELETE FROM custom_recipes WHERE id = ?", (recipe_id,))
    return cur.rowcount > 0


def food_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM foods").fetchone()
    return int(row["c"]) if row else 0
