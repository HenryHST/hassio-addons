"""DuckDB database schema and queries."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator, Iterator

import duckdb

KEY_NUTRIENTS = ("ENERCC", "ENERCJ", "CHO", "FAT", "PROT625", "FIBT", "NACL", "WATER")

_MIGRATION_TABLES = (
    "meta",
    "foods",
    "nutrients",
    "food_nutrients",
    "custom_foods",
    "custom_food_nutrients",
    "custom_recipes",
    "recipe_ingredients",
    "off_products",
    "off_search_cache",
    "off_barcode_miss",
    "favorites",
)


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


@contextmanager
def get_connection(db_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def _fetchone_dict(result: duckdb.DuckDBPyConnection) -> dict[str, Any] | None:
    row = result.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in result.description]
    return dict(zip(columns, row, strict=False))


def _fetchall_dicts(result: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = result.fetchall()
    if not rows:
        return []
    columns = [col[0] for col in result.description]
    return [dict(zip(columns, row, strict=False)) for row in rows]


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS foods (
            bls_code VARCHAR PRIMARY KEY,
            name_de VARCHAR NOT NULL,
            name_en VARCHAR
        );

        CREATE TABLE IF NOT EXISTS nutrients (
            code VARCHAR PRIMARY KEY,
            name_de VARCHAR,
            name_en VARCHAR,
            unit VARCHAR,
            nutrient_group VARCHAR
        );

        CREATE TABLE IF NOT EXISTS food_nutrients (
            bls_code VARCHAR NOT NULL,
            nutrient_code VARCHAR NOT NULL,
            value DOUBLE,
            provenance VARCHAR,
            reference VARCHAR,
            PRIMARY KEY (bls_code, nutrient_code)
        );

        CREATE TABLE IF NOT EXISTS custom_foods (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            notes VARCHAR,
            created_at VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS custom_food_nutrients (
            custom_food_id INTEGER NOT NULL,
            nutrient_code VARCHAR NOT NULL,
            value DOUBLE,
            PRIMARY KEY (custom_food_id, nutrient_code)
        );

        CREATE TABLE IF NOT EXISTS custom_recipes (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            servings INTEGER NOT NULL DEFAULT 1,
            created_at VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER NOT NULL,
            source_type VARCHAR NOT NULL,
            source_id VARCHAR NOT NULL,
            amount_g DOUBLE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS off_products (
            barcode VARCHAR PRIMARY KEY,
            name VARCHAR,
            brand VARCHAR,
            nutrients_json VARCHAR NOT NULL,
            fetched_at VARCHAR NOT NULL,
            nutriscore VARCHAR,
            nova_group INTEGER,
            ecoscore VARCHAR
        );

        CREATE TABLE IF NOT EXISTS off_search_cache (
            cache_key VARCHAR PRIMARY KEY,
            results_json VARCHAR NOT NULL,
            fetched_at VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS off_barcode_miss (
            barcode VARCHAR PRIMARY KEY,
            fetched_at VARCHAR NOT NULL
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            display_name VARCHAR NOT NULL,
            source_type VARCHAR NOT NULL,
            source_id VARCHAR NOT NULL,
            barcode VARCHAR,
            brand VARCHAR,
            default_amount_g DOUBLE NOT NULL DEFAULT 100,
            image_path VARCHAR,
            image_url VARCHAR,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL,
            UNIQUE(source_type, source_id)
        );
        """
    )
    set_meta(conn, "database_engine", "duckdb")


def ensure_foods_fts(conn: duckdb.DuckDBPyConnection) -> None:
    """No-op: DuckDB uses ILIKE/prefix search instead of SQLite FTS5."""


def rebuild_foods_fts(conn: duckdb.DuckDBPyConnection) -> None:
    """No-op for DuckDB."""


def set_meta(conn: duckdb.DuckDBPyConnection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO meta(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        [key, value],
    )


def get_meta(conn: duckdb.DuckDBPyConnection, key: str) -> str | None:
    row = _fetchone_dict(
        conn.execute("SELECT value FROM meta WHERE key = ?", [key])
    )
    return str(row["value"]) if row else None


def set_database_status(conn: duckdb.DuckDBPyConnection, status: str) -> None:
    set_meta(conn, "database_status", status)


def get_database_status(conn: duckdb.DuckDBPyConnection) -> str:
    return get_meta(conn, "database_status") or "ready"


def _food_rows_to_results(
    rows: list[dict[str, Any]], language: str
) -> list[dict[str, Any]]:
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


def _search_foods_like(
    conn: duckdb.DuckDBPyConnection, query: str, limit: int, language: str
) -> list[dict[str, Any]]:
    pattern = f"%{query.strip()}%"
    prefix = f"{query.strip()}%"
    rows = _fetchall_dicts(
        conn.execute(
            """
            SELECT bls_code, name_de, name_en
            FROM foods
            WHERE name_de ILIKE ? OR name_en ILIKE ? OR bls_code ILIKE ?
            ORDER BY
                CASE
                    WHEN name_de ILIKE ? THEN 0
                    WHEN name_en ILIKE ? THEN 1
                    ELSE 2
                END,
                name_de
            LIMIT ?
            """,
            [pattern, pattern, pattern, prefix, prefix, limit],
        )
    )
    return _food_rows_to_results(rows, language)


def search_foods(
    conn: duckdb.DuckDBPyConnection, query: str, limit: int = 20, language: str = "de"
) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []

    prefix_rows = _fetchall_dicts(
        conn.execute(
            """
            SELECT bls_code, name_de, name_en
            FROM foods
            WHERE bls_code ILIKE ?
            ORDER BY bls_code
            LIMIT ?
            """,
            [f"{q}%", limit],
        )
    )
    if prefix_rows:
        return _food_rows_to_results(prefix_rows, language)

    return _search_foods_like(conn, q, limit, language)


def get_food_name(
    conn: duckdb.DuckDBPyConnection, bls_code: str, language: str = "de"
) -> str | None:
    row = _fetchone_dict(
        conn.execute(
            "SELECT name_de, name_en FROM foods WHERE bls_code = ?", [bls_code]
        )
    )
    if not row:
        return None
    return row["name_de"] if language == "de" else (row["name_en"] or row["name_de"])


def get_nutrients_per_100g(
    conn: duckdb.DuckDBPyConnection, source: str, item_id: str
) -> dict[str, float | None]:
    if source == "bls":
        rows = _fetchall_dicts(
            conn.execute(
                """
                SELECT nutrient_code AS code, value
                FROM food_nutrients
                WHERE bls_code = ?
                """,
                [item_id],
            )
        )
        return {row["code"]: row["value"] for row in rows}

    if source == "custom":
        rows = _fetchall_dicts(
            conn.execute(
                """
                SELECT nutrient_code AS code, value
                FROM custom_food_nutrients
                WHERE custom_food_id = ?
                """,
                [int(item_id)],
            )
        )
        return {row["code"]: row["value"] for row in rows}

    if source == "off":
        row = _fetchone_dict(
            conn.execute(
                "SELECT nutrients_json FROM off_products WHERE barcode = ?", [item_id]
            )
        )
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
    conn: duckdb.DuckDBPyConnection,
    barcode: str,
    name: str | None,
    brand: str | None,
    nutrients: dict[str, float | None],
    *,
    nutriscore: str | None = None,
    nova_group: int | None = None,
    ecoscore: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO off_products(
            barcode, name, brand, nutrients_json, fetched_at,
            nutriscore, nova_group, ecoscore
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(barcode) DO UPDATE SET
            name = excluded.name,
            brand = excluded.brand,
            nutrients_json = excluded.nutrients_json,
            fetched_at = excluded.fetched_at,
            nutriscore = excluded.nutriscore,
            nova_group = excluded.nova_group,
            ecoscore = excluded.ecoscore
        """,
        [
            barcode,
            name,
            brand,
            json.dumps(nutrients),
            datetime.now(timezone.utc).isoformat(),
            nutriscore,
            nova_group,
            ecoscore,
        ],
    )
    conn.execute("DELETE FROM off_barcode_miss WHERE barcode = ?", [barcode])


def _off_search_cache_key(query: str, language: str, limit: int) -> str:
    return f"{query.strip().lower()}|{language}|{limit}"


def get_off_search_cache(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    language: str,
    limit: int,
    ttl_days: int,
) -> list[dict[str, Any]] | None:
    key = _off_search_cache_key(query, language, limit)
    row = _fetchone_dict(
        conn.execute(
            "SELECT results_json, fetched_at FROM off_search_cache WHERE cache_key = ?",
            [key],
        )
    )
    if not row:
        return None
    try:
        fetched = datetime.fromisoformat(str(row["fetched_at"]))
    except ValueError:
        return None
    if fetched <= datetime.now(timezone.utc) - timedelta(days=ttl_days):
        return None
    data = json.loads(row["results_json"])
    return data if isinstance(data, list) else None


def save_off_search_cache(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    language: str,
    limit: int,
    results: list[dict[str, Any]],
) -> None:
    key = _off_search_cache_key(query, language, limit)
    conn.execute(
        """
        INSERT INTO off_search_cache(cache_key, results_json, fetched_at)
        VALUES(?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            results_json = excluded.results_json,
            fetched_at = excluded.fetched_at
        """,
        [key, json.dumps(results), datetime.now(timezone.utc).isoformat()],
    )


def search_off_products_local(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []
    pattern = f"%{q}%"
    prefix = f"{q}%"
    rows = _fetchall_dicts(
        conn.execute(
            """
            SELECT barcode, name, brand, nutriscore, nova_group, ecoscore
            FROM off_products
            WHERE name ILIKE ? OR brand ILIKE ? OR barcode ILIKE ?
            ORDER BY
                CASE
                    WHEN name ILIKE ? THEN 0
                    WHEN brand ILIKE ? THEN 1
                    ELSE 2
                END,
                name
            LIMIT ?
            """,
            [pattern, pattern, pattern, prefix, prefix, limit],
        )
    )
    results: list[dict[str, Any]] = []
    for row in rows:
        name = row.get("name")
        if not name:
            continue
        results.append(
            {
                "source": "off",
                "id": row["barcode"],
                "name": name,
                "brand": row.get("brand"),
                "nutriscore": row.get("nutriscore"),
                "nova_group": row.get("nova_group"),
                "ecoscore": row.get("ecoscore"),
            }
        )
    return results


def is_off_barcode_miss(
    conn: duckdb.DuckDBPyConnection, barcode: str, ttl_days: int
) -> bool:
    row = _fetchone_dict(
        conn.execute(
            "SELECT fetched_at FROM off_barcode_miss WHERE barcode = ?", [barcode]
        )
    )
    if not row:
        return False
    try:
        fetched = datetime.fromisoformat(str(row["fetched_at"]))
    except ValueError:
        return False
    return fetched > datetime.now(timezone.utc) - timedelta(days=ttl_days)


def save_off_barcode_miss(conn: duckdb.DuckDBPyConnection, barcode: str) -> None:
    conn.execute(
        """
        INSERT INTO off_barcode_miss(barcode, fetched_at)
        VALUES(?, ?)
        ON CONFLICT(barcode) DO UPDATE SET fetched_at = excluded.fetched_at
        """,
        [barcode, datetime.now(timezone.utc).isoformat()],
    )


def get_off_product(conn: duckdb.DuckDBPyConnection, barcode: str) -> dict[str, Any] | None:
    row = _fetchone_dict(
        conn.execute(
            """
            SELECT barcode, name, brand, nutrients_json, fetched_at,
                   nutriscore, nova_group, ecoscore
            FROM off_products WHERE barcode = ?
            """,
            [barcode],
        )
    )
    if not row:
        return None
    return {
        "source": "off",
        "id": row["barcode"],
        "name": row["name"],
        "brand": row["brand"],
        "nutrients": json.loads(row["nutrients_json"]),
        "fetched_at": row["fetched_at"],
        "nutriscore": row["nutriscore"],
        "nova_group": row["nova_group"],
        "ecoscore": row["ecoscore"],
    }


def list_custom_foods(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return _fetchall_dicts(
        conn.execute(
            "SELECT id, name, notes, created_at FROM custom_foods ORDER BY name"
        )
    )


def get_custom_food(conn: duckdb.DuckDBPyConnection, food_id: int) -> dict[str, Any] | None:
    row = _fetchone_dict(
        conn.execute(
            "SELECT id, name, notes, created_at FROM custom_foods WHERE id = ?",
            [food_id],
        )
    )
    if not row:
        return None
    nutrients = get_nutrients_per_100g(conn, "custom", str(food_id))
    return {**row, "nutrients": nutrients}


def _next_custom_food_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM custom_foods"))
    return int(row["next_id"]) if row else 1


def create_custom_food(
    conn: duckdb.DuckDBPyConnection, name: str, notes: str | None, nutrients: dict[str, float]
) -> int:
    food_id = _next_custom_food_id(conn)
    conn.execute(
        "INSERT INTO custom_foods(id, name, notes, created_at) VALUES(?, ?, ?, ?)",
        [food_id, name, notes, datetime.now(timezone.utc).isoformat()],
    )
    for code, value in nutrients.items():
        conn.execute(
            "INSERT INTO custom_food_nutrients(custom_food_id, nutrient_code, value) VALUES(?, ?, ?)",
            [food_id, code, value],
        )
    return food_id


def update_custom_food(
    conn: duckdb.DuckDBPyConnection,
    food_id: int,
    name: str | None,
    notes: str | None,
    nutrients: dict[str, float] | None,
) -> bool:
    row = _fetchone_dict(
        conn.execute("SELECT id FROM custom_foods WHERE id = ?", [food_id])
    )
    if not row:
        return False
    if name is not None:
        conn.execute("UPDATE custom_foods SET name = ? WHERE id = ?", [name, food_id])
    if notes is not None:
        conn.execute("UPDATE custom_foods SET notes = ? WHERE id = ?", [notes, food_id])
    if nutrients is not None:
        conn.execute(
            "DELETE FROM custom_food_nutrients WHERE custom_food_id = ?", [food_id]
        )
        for code, value in nutrients.items():
            conn.execute(
                "INSERT INTO custom_food_nutrients(custom_food_id, nutrient_code, value) VALUES(?, ?, ?)",
                [food_id, code, value],
            )
    return True


def delete_custom_food(conn: duckdb.DuckDBPyConnection, food_id: int) -> bool:
    row = _fetchone_dict(
        conn.execute("SELECT id FROM custom_foods WHERE id = ?", [food_id])
    )
    if not row:
        return False
    conn.execute(
        "DELETE FROM custom_food_nutrients WHERE custom_food_id = ?", [food_id]
    )
    conn.execute("DELETE FROM custom_foods WHERE id = ?", [food_id])
    return True


def list_custom_recipes(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return _fetchall_dicts(
        conn.execute(
            "SELECT id, name, servings, created_at FROM custom_recipes ORDER BY name"
        )
    )


def get_custom_recipe(conn: duckdb.DuckDBPyConnection, recipe_id: int) -> dict[str, Any] | None:
    row = _fetchone_dict(
        conn.execute(
            "SELECT id, name, servings, created_at FROM custom_recipes WHERE id = ?",
            [recipe_id],
        )
    )
    if not row:
        return None
    ingredients = _fetchall_dicts(
        conn.execute(
            """
            SELECT source_type AS source, source_id AS id, amount_g
            FROM recipe_ingredients WHERE recipe_id = ?
            """,
            [recipe_id],
        )
    )
    return {**row, "ingredients": ingredients}


def _next_custom_recipe_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(
        conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM custom_recipes")
    )
    return int(row["next_id"]) if row else 1


def create_custom_recipe(
    conn: duckdb.DuckDBPyConnection,
    name: str,
    servings: int,
    ingredients: list[dict[str, Any]],
) -> int:
    recipe_id = _next_custom_recipe_id(conn)
    conn.execute(
        "INSERT INTO custom_recipes(id, name, servings, created_at) VALUES(?, ?, ?, ?)",
        [recipe_id, name, servings, datetime.now(timezone.utc).isoformat()],
    )
    for ingredient in ingredients:
        conn.execute(
            """
            INSERT INTO recipe_ingredients(recipe_id, source_type, source_id, amount_g)
            VALUES(?, ?, ?, ?)
            """,
            [
                recipe_id,
                ingredient["source"],
                ingredient["id"],
                ingredient["amount_g"],
            ],
        )
    return recipe_id


def delete_custom_recipe(conn: duckdb.DuckDBPyConnection, recipe_id: int) -> bool:
    conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", [recipe_id])
    row = _fetchone_dict(
        conn.execute(
            "DELETE FROM custom_recipes WHERE id = ? RETURNING id", [recipe_id]
        )
    )
    return row is not None


def food_count(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(conn.execute("SELECT COUNT(*) AS c FROM foods"))
    return int(row["c"]) if row else 0


def off_products_count(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(conn.execute("SELECT COUNT(*) AS c FROM off_products"))
    return int(row["c"]) if row else 0


def purge_expired_cache(
    conn: duckdb.DuckDBPyConnection,
    off_cache_ttl_days: int,
    off_search_cache_ttl_days: int,
) -> None:
    now = datetime.now(timezone.utc)
    off_cutoff = (now - timedelta(days=off_cache_ttl_days)).isoformat()
    search_cutoff = (now - timedelta(days=off_search_cache_ttl_days)).isoformat()
    conn.execute("DELETE FROM off_products WHERE fetched_at < ?", [off_cutoff])
    conn.execute("DELETE FROM off_search_cache WHERE fetched_at < ?", [search_cutoff])
    conn.execute("DELETE FROM off_barcode_miss WHERE fetched_at < ?", [off_cutoff])


def migrate_from_sqlite(sqlite_path: Path, duckdb_path: Path) -> None:
    """One-time migration from legacy bls.sqlite to bls.duckdb."""
    if duckdb_path.exists():
        return
    if not sqlite_path.is_file():
        return

    print(f"[bls-db] Migrating {sqlite_path} -> {duckdb_path}")
    conn = connect(duckdb_path)
    init_schema(conn)
    conn.execute("INSTALL sqlite;")
    conn.execute("LOAD sqlite;")
    sqlite_escaped = str(sqlite_path).replace("'", "''")
    conn.execute(f"ATTACH '{sqlite_escaped}' AS legacy (TYPE SQLITE, READ_ONLY)")

    for table in _MIGRATION_TABLES:
        try:
            conn.execute(f"INSERT INTO main.{table} SELECT * FROM legacy.{table}")
            print(f"[bls-db] Migrated table {table}")
        except duckdb.Error as exc:
            print(f"[bls-db] Skip table {table}: {exc}")

    conn.execute("DETACH legacy")
    set_meta(conn, "database_engine", "duckdb")
    set_meta(conn, "database_status", "ready")
    set_meta(conn, "migrated_from_sqlite_at", datetime.now(timezone.utc).isoformat())
    conn.close()
    print("[bls-db] Migration complete")


def favorites_count(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(conn.execute("SELECT COUNT(*) AS c FROM favorites"))
    return int(row["c"]) if row else 0


def _next_favorite_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = _fetchone_dict(
        conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM favorites")
    )
    return int(row["next_id"]) if row else 1


def _favorite_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "display_name": row["display_name"],
        "source": row["source_type"],
        "source_id": row["source_id"],
        "barcode": row.get("barcode"),
        "brand": row.get("brand"),
        "default_amount_g": float(row["default_amount_g"]),
        "image_path": row.get("image_path"),
        "image_url": row.get("image_url"),
        "sort_order": int(row["sort_order"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_favorites(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = _fetchall_dicts(
        conn.execute(
            """
            SELECT * FROM favorites
            ORDER BY sort_order ASC, display_name ASC, id ASC
            """
        )
    )
    return [_favorite_from_row(row) for row in rows]


def get_favorite(conn: duckdb.DuckDBPyConnection, favorite_id: int) -> dict[str, Any] | None:
    row = _fetchone_dict(
        conn.execute("SELECT * FROM favorites WHERE id = ?", [favorite_id])
    )
    return _favorite_from_row(row) if row else None


def get_favorite_by_source(
    conn: duckdb.DuckDBPyConnection, source_type: str, source_id: str
) -> dict[str, Any] | None:
    row = _fetchone_dict(
        conn.execute(
            "SELECT * FROM favorites WHERE source_type = ? AND source_id = ?",
            [source_type, source_id],
        )
    )
    return _favorite_from_row(row) if row else None


def create_favorite(
    conn: duckdb.DuckDBPyConnection,
    display_name: str,
    source_type: str,
    source_id: str,
    *,
    barcode: str | None = None,
    brand: str | None = None,
    default_amount_g: float = 100.0,
) -> dict[str, Any]:
    existing = get_favorite_by_source(conn, source_type, source_id)
    if existing:
        return existing
    now = datetime.now(timezone.utc).isoformat()
    favorite_id = _next_favorite_id(conn)
    sort_row = _fetchone_dict(
        conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM favorites")
    )
    sort_order = int(sort_row["next_order"]) if sort_row else 0
    conn.execute(
        """
        INSERT INTO favorites(
            id, display_name, source_type, source_id, barcode, brand,
            default_amount_g, sort_order, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            favorite_id,
            display_name,
            source_type,
            source_id,
            barcode,
            brand,
            default_amount_g,
            sort_order,
            now,
            now,
        ],
    )
    favorite = get_favorite(conn, favorite_id)
    if not favorite:
        raise RuntimeError("Failed to create favorite")
    return favorite


def update_favorite(
    conn: duckdb.DuckDBPyConnection,
    favorite_id: int,
    *,
    display_name: str | None = None,
    default_amount_g: float | None = None,
    image_path: str | None = None,
    image_url: str | None = None,
    clear_image_path: bool = False,
    clear_image_url: bool = False,
) -> dict[str, Any] | None:
    favorite = get_favorite(conn, favorite_id)
    if not favorite:
        return None
    if display_name is not None:
        conn.execute(
            "UPDATE favorites SET display_name = ? WHERE id = ?",
            [display_name, favorite_id],
        )
    if default_amount_g is not None:
        conn.execute(
            "UPDATE favorites SET default_amount_g = ? WHERE id = ?",
            [default_amount_g, favorite_id],
        )
    if clear_image_path:
        conn.execute("UPDATE favorites SET image_path = NULL WHERE id = ?", [favorite_id])
    elif image_path is not None:
        conn.execute(
            "UPDATE favorites SET image_path = ? WHERE id = ?",
            [image_path, favorite_id],
        )
    if clear_image_url:
        conn.execute("UPDATE favorites SET image_url = NULL WHERE id = ?", [favorite_id])
    elif image_url is not None:
        conn.execute(
            "UPDATE favorites SET image_url = ? WHERE id = ?",
            [image_url, favorite_id],
        )
    conn.execute(
        "UPDATE favorites SET updated_at = ? WHERE id = ?",
        [datetime.now(timezone.utc).isoformat(), favorite_id],
    )
    return get_favorite(conn, favorite_id)


def delete_favorite(conn: duckdb.DuckDBPyConnection, favorite_id: int) -> bool:
    row = _fetchone_dict(
        conn.execute("SELECT id FROM favorites WHERE id = ?", [favorite_id])
    )
    if not row:
        return False
    conn.execute("DELETE FROM favorites WHERE id = ?", [favorite_id])
    return True


def delete_favorite_by_source(
    conn: duckdb.DuckDBPyConnection, source_type: str, source_id: str
) -> bool:
    row = _fetchone_dict(
        conn.execute(
            "SELECT id FROM favorites WHERE source_type = ? AND source_id = ?",
            [source_type, source_id],
        )
    )
    if not row:
        return False
    conn.execute(
        "DELETE FROM favorites WHERE source_type = ? AND source_id = ?",
        [source_type, source_id],
    )
    return True
