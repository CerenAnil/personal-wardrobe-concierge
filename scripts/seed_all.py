"""
Seed pipeline — loads wardrobe_items.json into SQLite and ChromaDB.
Neo4j seeding is Phase 2 (run scripts/seed_neo4j.py).

Usage:
  python scripts/seed_all.py
  python scripts/seed_all.py --reset      # wipe and re-seed ChromaDB
"""

import argparse
import json
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.db.sqlite_client import init_db, upsert_item, get_all_items
from src.db.chroma_client import upsert_items, reset_collection, count


ITEMS_PATH = os.path.join("data", "seed", "wardrobe_items.json")


def load_items() -> list[dict]:
    if not os.path.exists(ITEMS_PATH):
        raise FileNotFoundError(
            f"{ITEMS_PATH} not found. Run: python scripts/generate_seed_data.py"
        )
    with open(ITEMS_PATH) as f:
        return json.load(f)


def seed_sqlite(items: list[dict]) -> None:
    print("Seeding SQLite...")
    init_db()
    for item in items:
        upsert_item(item)
    stored = get_all_items()
    print(f"  SQLite: {len(stored)} items stored")


def seed_chroma(items: list[dict], reset: bool = False) -> None:
    print("Seeding ChromaDB...")
    if reset:
        print("  Resetting collection...")
        reset_collection()
    upsert_items(items)
    n = count()
    print(f"  ChromaDB: {n} embeddings stored")


def main():
    parser = argparse.ArgumentParser(description="Seed SQLite + ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Wipe ChromaDB before seeding")
    args = parser.parse_args()

    items = load_items()
    print(f"Loaded {len(items)} items from {ITEMS_PATH}")

    # Normalise: both sqlite_client and chroma_client expect key "id"
    for item in items:
        if "id" not in item and "item_id" in item:
            item["id"] = item["item_id"]

    seed_sqlite(items)
    seed_chroma(items, reset=args.reset)

    print("\nDone. Next: python scripts/seed_neo4j.py (Phase 2)")


if __name__ == "__main__":
    main()
