"""
Neo4j seed pipeline - builds the outfit compatibility graph.

Run after generate_seed_data.py and seed_all.py.

Usage:
  python scripts/seed_neo4j.py
  python scripts/seed_neo4j.py --wipe   # drop all nodes/rels first

Node types:   Item, Occasion, Season, ColorPalette, StyleCluster
Relationships seeded from data:
  SUITABLE_FOR   Item -> Occasion       (from item.occasions)
  WORN_IN        Item -> Season         (from item.seasons)
  BELONGS_TO_PALETTE  Item -> ColorPalette  (from item.color_family)
  HAS_STYLE      Item -> StyleCluster   (from item.style_tags)

Computed relationships (style rules):
  PAIRS_WITH     Item -> Item   (color-compatible + formality +-1 + different category)
  CLASHES_WITH   Item -> Item   (cool+warm color clash OR formality gap >= 3)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.db.neo4j_client import run_write, run_query, close

ITEMS_PATH = os.path.join("data", "seed", "wardrobe_items.json")

# ---------------------------------------------------------------------------
# Color compatibility rules
# ---------------------------------------------------------------------------
# Palette adjacency: set of families that pair well together
COLOR_COMPATIBLE: dict[str, set[str]] = {
    "neutral": {"neutral", "cool", "warm", "earth"},
    "cool":    {"cool", "neutral"},
    "warm":    {"warm", "neutral", "earth"},
    "earth":   {"earth", "warm", "neutral"},
}


def colors_compatible(a: str, b: str) -> bool:
    return b in COLOR_COMPATIBLE.get(a, set())


def colors_clash(a: str, b: str) -> bool:
    """cool + warm (both non-neutral) is a clash."""
    cool_warm = {"cool", "warm"}
    return a in cool_warm and b in cool_warm and a != b


# ---------------------------------------------------------------------------
# PAIRS_WITH / CLASHES_WITH rules
# ---------------------------------------------------------------------------
def should_pair(a: dict, b: dict) -> bool:
    """
    True if a and b are styling-compatible:
    - Different categories (or both accessories — accessories always pair)
    - Color families are compatible
    - Formality within +-1
    """
    if a["id"] == b["id"]:
        return False
    cat_a, cat_b = a["category"], b["category"]
    # Same non-accessory category doesn't produce a pair
    if cat_a == cat_b and cat_a != "accessories":
        return False
    if not colors_compatible(a["color_family"], b["color_family"]):
        return False
    if abs(a["formality"] - b["formality"]) > 1:
        return False
    return True


def should_clash(a: dict, b: dict) -> bool:
    """
    True if a and b have a styling conflict:
    - cool + warm color clash, or
    - formality gap >= 3 (e.g. gym shorts + black tie shoes)
    """
    if a["id"] == b["id"]:
        return False
    if colors_clash(a["color_family"], b["color_family"]):
        return True
    if abs(a["formality"] - b["formality"]) >= 3:
        return True
    return False


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------
def wipe(verbose: bool = True) -> None:
    run_write("MATCH (n) DETACH DELETE n")
    if verbose:
        print("  Wiped all nodes and relationships")


def seed_constraints() -> None:
    constraints = [
        "CREATE CONSTRAINT item_id IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT occasion_name IF NOT EXISTS FOR (o:Occasion) REQUIRE o.name IS UNIQUE",
        "CREATE CONSTRAINT season_name IF NOT EXISTS FOR (s:Season) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT palette_name IF NOT EXISTS FOR (p:ColorPalette) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT style_name IF NOT EXISTS FOR (s:StyleCluster) REQUIRE s.name IS UNIQUE",
    ]
    for c in constraints:
        try:
            run_write(c)
        except Exception as e:
            # Ignore duplicate constraint errors on re-run
            if "already exists" not in str(e).lower():
                raise


def seed_items(items: list[dict]) -> None:
    for item in items:
        run_write(
            """
            MERGE (i:Item {id: $id})
            SET i.name        = $name,
                i.category    = $category,
                i.subcategory = $subcategory,
                i.formality   = $formality,
                i.color       = $color,
                i.color_family = $color_family,
                i.material    = $material,
                i.style_tags  = $style_tags,
                i.owned_since = $owned_since,
                i.last_worn   = $last_worn
            """,
            {
                "id":          item["id"],
                "name":        item["name"],
                "category":    item["category"],
                "subcategory": item.get("subcategory", ""),
                "formality":   item["formality"],
                "color":       item["color"],
                "color_family": item["color_family"],
                "material":    item.get("material", ""),
                "style_tags":  ",".join(item.get("style_tags", [])),
                "owned_since": item.get("owned_since") or "",
                "last_worn":   item.get("last_worn") or "",
            },
        )


def seed_occasions_and_rels(items: list[dict]) -> None:
    occasions: set[str] = set()
    for item in items:
        for occ in item.get("occasions", []):
            occasions.add(occ)

    for occ in occasions:
        run_write("MERGE (:Occasion {name: $name})", {"name": occ})

    for item in items:
        for occ in item.get("occasions", []):
            run_write(
                """
                MATCH (i:Item {id: $item_id}), (o:Occasion {name: $occ})
                MERGE (i)-[:SUITABLE_FOR]->(o)
                """,
                {"item_id": item["id"], "occ": occ},
            )


def seed_seasons_and_rels(items: list[dict]) -> None:
    seasons = {"spring", "summer", "autumn", "winter"}
    for s in seasons:
        run_write("MERGE (:Season {name: $name})", {"name": s})

    for item in items:
        for s in item.get("seasons", []):
            run_write(
                """
                MATCH (i:Item {id: $item_id}), (s:Season {name: $season})
                MERGE (i)-[:WORN_IN]->(s)
                """,
                {"item_id": item["id"], "season": s},
            )


def seed_palettes_and_rels(items: list[dict]) -> None:
    palettes = {"cool", "warm", "neutral", "earth", "monochrome"}
    for p in palettes:
        run_write("MERGE (:ColorPalette {name: $name})", {"name": p})

    for item in items:
        cf = item.get("color_family", "neutral")
        run_write(
            """
            MATCH (i:Item {id: $item_id}), (p:ColorPalette {name: $palette})
            MERGE (i)-[:BELONGS_TO_PALETTE]->(p)
            """,
            {"item_id": item["id"], "palette": cf},
        )


def seed_style_clusters_and_rels(items: list[dict]) -> None:
    clusters: set[str] = set()
    for item in items:
        for tag in item.get("style_tags", []):
            clusters.add(tag)

    for tag in clusters:
        run_write("MERGE (:StyleCluster {name: $name})", {"name": tag})

    for item in items:
        for tag in item.get("style_tags", []):
            run_write(
                """
                MATCH (i:Item {id: $item_id}), (s:StyleCluster {name: $tag})
                MERGE (i)-[:HAS_STYLE]->(s)
                """,
                {"item_id": item["id"], "tag": tag},
            )


def seed_pairs_with(items: list[dict]) -> int:
    count = 0
    for i, a in enumerate(items):
        for b in items[i + 1:]:   # upper triangle only; MERGE is undirected
            if should_pair(a, b):
                run_write(
                    """
                    MATCH (a:Item {id: $id_a}), (b:Item {id: $id_b})
                    MERGE (a)-[:PAIRS_WITH]->(b)
                    """,
                    {"id_a": a["id"], "id_b": b["id"]},
                )
                count += 1
    return count


def seed_clashes_with(items: list[dict]) -> int:
    count = 0
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if should_clash(a, b):
                run_write(
                    """
                    MATCH (a:Item {id: $id_a}), (b:Item {id: $id_b})
                    MERGE (a)-[:CLASHES_WITH]->(b)
                    """,
                    {"id_a": a["id"], "id_b": b["id"]},
                )
                count += 1
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="Delete all nodes before seeding")
    args = parser.parse_args()

    if not os.path.exists(ITEMS_PATH):
        raise FileNotFoundError(
            f"{ITEMS_PATH} not found. Run: python scripts/generate_seed_data.py"
        )

    with open(ITEMS_PATH) as f:
        items = json.load(f)

    print(f"Loaded {len(items)} items")

    if args.wipe:
        print("Wiping graph...")
        wipe()

    print("Creating constraints...")
    seed_constraints()

    print("Seeding Item nodes...")
    seed_items(items)
    print(f"  {len(items)} Item nodes")

    print("Seeding Occasion nodes + SUITABLE_FOR...")
    seed_occasions_and_rels(items)

    print("Seeding Season nodes + WORN_IN...")
    seed_seasons_and_rels(items)

    print("Seeding ColorPalette nodes + BELONGS_TO_PALETTE...")
    seed_palettes_and_rels(items)

    print("Seeding StyleCluster nodes + HAS_STYLE...")
    seed_style_clusters_and_rels(items)

    print("Computing PAIRS_WITH edges...")
    n_pairs = seed_pairs_with(items)
    print(f"  {n_pairs} PAIRS_WITH relationships")

    print("Computing CLASHES_WITH edges...")
    n_clashes = seed_clashes_with(items)
    print(f"  {n_clashes} CLASHES_WITH relationships")

    # Verify
    counts = run_query("MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS n ORDER BY n DESC")
    print("\nGraph summary:")
    for row in counts:
        print(f"  {row['rel']:25s} {row['n']}")

    close()
    print("\nNeo4j seed complete.")


if __name__ == "__main__":
    main()
