"""
SQLite client — wardrobe items, wear log, and outfit sessions.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional

DB_PATH = os.getenv("SQLITE_DB_PATH", "data/seed/wardrobe.db")


@contextmanager
def _conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    subcategory TEXT,
    color       TEXT,
    color_family TEXT,
    material    TEXT,
    formality   INTEGER,
    occasions   TEXT,       -- JSON list
    seasons     TEXT,       -- JSON list
    style_tags  TEXT,       -- JSON list
    owned_since TEXT,
    last_worn   TEXT,
    notes       TEXT,
    image_path  TEXT,
    active      INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS wear_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         TEXT NOT NULL,
    outfit_id       TEXT,
    occasion        TEXT,
    worn_on         TEXT,
    weather_summary TEXT,
    user_rating     INTEGER,
    notes           TEXT,
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS outfits (
    id           TEXT PRIMARY KEY,
    occasion     TEXT,
    context_json TEXT,
    item_ids     TEXT,       -- JSON list
    worn_on      TEXT,
    approved     INTEGER DEFAULT 0
);
"""


def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------
def upsert_item(item: dict, db_path: str = DB_PATH) -> None:
    sql = """
    INSERT OR REPLACE INTO items
        (id, name, category, subcategory, color, color_family, material,
         formality, occasions, seasons, style_tags, owned_since, last_worn,
         notes, image_path, active)
    VALUES
        (:id, :name, :category, :subcategory, :color, :color_family, :material,
         :formality, :occasions, :seasons, :style_tags, :owned_since, :last_worn,
         :notes, :image_path, :active)
    """
    row = {**item}
    for field in ("occasions", "seasons", "style_tags"):
        if isinstance(row.get(field), list):
            row[field] = json.dumps(row[field])
    row.setdefault("active", 1)
    with _conn(db_path) as conn:
        conn.execute(sql, row)


def get_item(item_id: str, db_path: str = DB_PATH) -> Optional[dict]:
    with _conn(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ? AND active = 1", (item_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def search_items(
    query: str = "",
    category: Optional[str] = None,
    formality_min: Optional[int] = None,
    formality_max: Optional[int] = None,
    season: Optional[str] = None,
    occasion: Optional[str] = None,
    limit: int = 20,
    db_path: str = DB_PATH,
) -> list[dict]:
    """Simple SQL filter search — hybrid search (BM25+vector) lives in retrieval/."""
    clauses = ["active = 1"]
    params: list = []

    if category:
        clauses.append("category = ?")
        params.append(category)
    if formality_min is not None:
        clauses.append("formality >= ?")
        params.append(formality_min)
    if formality_max is not None:
        clauses.append("formality <= ?")
        params.append(formality_max)
    if season:
        clauses.append("seasons LIKE ?")
        params.append(f'%"{season}"%')
    if occasion:
        clauses.append("occasions LIKE ?")
        params.append(f'%"{occasion}"%')
    if query:
        clauses.append(
            "(name LIKE ? OR subcategory LIKE ? OR color LIKE ? OR style_tags LIKE ? OR notes LIKE ?)"
        )
        like = f"%{query}%"
        params.extend([like, like, like, like, like])

    where = " AND ".join(clauses)
    sql = f"SELECT * FROM items WHERE {where} ORDER BY formality DESC LIMIT ?"
    params.append(limit)

    with _conn(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_all_items(db_path: str = DB_PATH) -> list[dict]:
    with _conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM items WHERE active = 1").fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Wear log
# ---------------------------------------------------------------------------
def log_wear(
    item_id: str,
    outfit_id: str,
    occasion: str,
    worn_on: str,
    weather_summary: str = "",
    notes: str = "",
    db_path: str = DB_PATH,
) -> None:
    with _conn(db_path) as conn:
        conn.execute(
            """INSERT INTO wear_log (item_id, outfit_id, occasion, worn_on, weather_summary, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_id, outfit_id, occasion, worn_on, weather_summary, notes),
        )
        conn.execute(
            "UPDATE items SET last_worn = ? WHERE id = ?", (worn_on, item_id)
        )


def get_wear_history(
    item_id: str, limit: int = 10, db_path: str = DB_PATH
) -> list[dict]:
    with _conn(db_path) as conn:
        rows = conn.execute(
            """SELECT * FROM wear_log WHERE item_id = ?
               ORDER BY worn_on DESC LIMIT ?""",
            (item_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Outfits
# ---------------------------------------------------------------------------
def save_outfit(outfit: dict, db_path: str = DB_PATH) -> None:
    row = {**outfit}
    if isinstance(row.get("item_ids"), list):
        row["item_ids"] = json.dumps(row["item_ids"])
    if isinstance(row.get("context_json"), dict):
        row["context_json"] = json.dumps(row["context_json"])
    with _conn(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO outfits (id, occasion, context_json, item_ids, worn_on, approved)
               VALUES (:id, :occasion, :context_json, :item_ids, :worn_on, :approved)""",
            row,
        )


def approve_outfit(outfit_id: str, db_path: str = DB_PATH) -> None:
    with _conn(db_path) as conn:
        conn.execute(
            "UPDATE outfits SET approved = 1 WHERE id = ?", (outfit_id,)
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for field in ("occasions", "seasons", "style_tags"):
        if isinstance(d.get(field), str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
