"""
Graph retrieval — 3 Cypher query patterns over the Neo4j outfit graph.

Pattern 1: PAIRS_WITH neighbors for a seed item (outfit building)
Pattern 2: Past successful outfits for the same occasion (wear history)
Pattern 3: Color palette coherence for a proposed outfit
"""

from __future__ import annotations

from dataclasses import dataclass

from src.db.neo4j_client import run_query


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass
class GraphItem:
    item_id: str
    name: str
    category: str
    formality: int
    color_family: str
    style_tags: list[str]


@dataclass
class PastOutfit:
    outfit_id: str
    worn_on: str
    rating: int
    items: list[GraphItem]


@dataclass
class PaletteCoherence:
    dominant_palette: str
    palette_counts: dict[str, int]
    is_coherent: bool   # True if >50% items share one palette or are neutral


# ---------------------------------------------------------------------------
# Pattern 1: Items that pair well with a seed item
# ---------------------------------------------------------------------------
def get_pairs_for_item(seed_id: str, limit: int = 10) -> list[GraphItem]:
    """
    Find items with PAIRS_WITH relationship to the seed, excluding CLASHES_WITH.
    Returns ordered by formality DESC.
    """
    cypher = """
    MATCH (seed:Item {id: $seed_id})-[:PAIRS_WITH]->(candidate:Item)
    WHERE NOT (seed)-[:CLASHES_WITH]-(candidate)
    RETURN candidate
    ORDER BY candidate.formality DESC
    LIMIT $limit
    """
    rows = run_query(cypher, {"seed_id": seed_id, "limit": limit})
    return [_to_graph_item(r["candidate"]) for r in rows]


# ---------------------------------------------------------------------------
# Pattern 2: Past successful outfits for an occasion
# ---------------------------------------------------------------------------
def get_past_outfits_for_occasion(occasion: str, min_rating: int = 4, limit: int = 5) -> list[PastOutfit]:
    """
    Find Outfit nodes worn for this occasion with rating >= min_rating.
    Returns items in each outfit, newest first.
    """
    cypher = """
    MATCH (o:Outfit)-[:SUITABLE_FOR]->(occ:Occasion {name: $occasion})
    MATCH (i:Item)-[:PART_OF]->(o)
    WHERE o.rating >= $min_rating
    RETURN o, collect(i) AS items
    ORDER BY o.worn_on DESC
    LIMIT $limit
    """
    rows = run_query(cypher, {"occasion": occasion, "min_rating": min_rating, "limit": limit})
    results = []
    for row in rows:
        o = row["o"]
        results.append(PastOutfit(
            outfit_id=o.get("id", ""),
            worn_on=o.get("worn_on", ""),
            rating=int(o.get("rating", 0)),
            items=[_to_graph_item(i) for i in row["items"]],
        ))
    return results


# ---------------------------------------------------------------------------
# Pattern 3: Color palette coherence
# ---------------------------------------------------------------------------
def check_palette_coherence(proposed_ids: list[str]) -> PaletteCoherence:
    """
    Given a list of proposed item IDs, check whether their color palettes are coherent.
    Returns dominant palette and whether >50% share one palette (or are neutral).
    """
    cypher = """
    MATCH (i:Item)-[:BELONGS_TO_PALETTE]->(p:ColorPalette)
    WHERE i.id IN $proposed_ids
    RETURN p.name AS palette, count(i) AS n
    ORDER BY n DESC
    """
    rows = run_query(cypher, {"proposed_ids": proposed_ids})
    counts = {r["palette"]: r["n"] for r in rows}

    dominant = rows[0]["palette"] if rows else "neutral"
    total = sum(counts.values())
    # Outfits are coherent if the dominant (or neutral) palette covers >50% of items
    dominant_count = counts.get(dominant, 0) + counts.get("neutral", 0)
    is_coherent = (dominant_count / total >= 0.5) if total > 0 else True

    return PaletteCoherence(
        dominant_palette=dominant,
        palette_counts=counts,
        is_coherent=is_coherent,
    )


# ---------------------------------------------------------------------------
# Pattern 4 (bonus): Items worn together with a seed (actual wear history)
# ---------------------------------------------------------------------------
def get_worn_together(seed_id: str, limit: int = 10) -> list[GraphItem]:
    """
    Items that have been worn in the same outfit as the seed item.
    Written by record_wear node after HITL approval.
    """
    cypher = """
    MATCH (seed:Item {id: $seed_id})-[:WORN_TOGETHER]-(partner:Item)
    RETURN partner, count(*) AS times
    ORDER BY times DESC
    LIMIT $limit
    """
    rows = run_query(cypher, {"seed_id": seed_id, "limit": limit})
    return [_to_graph_item(r["partner"]) for r in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_graph_item(node: dict) -> GraphItem:
    tags = node.get("style_tags", "")
    if isinstance(tags, str):
        tags = [t for t in tags.split(",") if t]
    return GraphItem(
        item_id=node.get("id", ""),
        name=node.get("name", ""),
        category=node.get("category", ""),
        formality=int(node.get("formality", 1)),
        color_family=node.get("color_family", "neutral"),
        style_tags=tags,
    )
