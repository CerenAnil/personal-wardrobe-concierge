"""
Hybrid search: BM25 + ChromaDB vector, fused with Reciprocal Rank Fusion (k=60).

Document format (same for both corpora):
  "{name} {subcategory} {color} {material} {occasions} {style_tags} {notes}"

Confidence: top result's RRF score / max possible RRF score (both systems rank it #1).
Confidence < 0.6 signals the calling agent to retry with relaxed filters.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.db.sqlite_client import get_all_items
from src.db.chroma_client import query_items as chroma_query

RRF_K = 60
# Maximum possible RRF score: top-1 in both BM25 and vector
MAX_RRF = (1.0 / (RRF_K + 1)) * 2


@dataclass
class HybridItem:
    item_id: str
    name: str
    category: str
    subcategory: str
    color: str
    color_family: str
    formality: int
    occasions: list[str]
    seasons: list[str]
    style_tags: list[str]
    notes: str
    rrf_score: float
    # Convenience accessors used by agents
    metadata: dict = field(default_factory=dict)


@dataclass
class HybridSearchResult:
    items: list[HybridItem]
    confidence: float           # top result score / MAX_RRF
    query: str
    retry_count: int = 0


# ---------------------------------------------------------------------------
# Corpus management (lazy-loaded, module-level cache)
# ---------------------------------------------------------------------------
_corpus_items: list[dict] | None = None
_bm25: BM25Okapi | None = None


def _build_document(item: dict) -> str:
    """Identical to chroma_client._item_to_document — keep in sync."""
    parts = [
        item.get("name", ""),
        item.get("subcategory", ""),
        item.get("color", ""),
        item.get("material", ""),
        _join(item, "occasions"),
        _join(item, "style_tags"),
        item.get("notes", ""),
    ]
    return " ".join(p for p in parts if p)


def _join(item: dict, key: str) -> str:
    val = item.get(key, [])
    if isinstance(val, list):
        return " ".join(val)
    return str(val)


def _load_corpus() -> tuple[list[dict], BM25Okapi]:
    global _corpus_items, _bm25
    if _corpus_items is None:
        _corpus_items = get_all_items()
        docs = [_build_document(i).lower().split() for i in _corpus_items]
        _bm25 = BM25Okapi(docs)
    return _corpus_items, _bm25  # type: ignore[return-value]


def reload_corpus() -> None:
    """Force reload — call after wardrobe import."""
    global _corpus_items, _bm25
    _corpus_items = None
    _bm25 = None


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------
def _rrf(rank: int, k: int = RRF_K) -> float:
    return 1.0 / (k + rank + 1)   # +1 so rank 0 = 1/(k+1)


def _bm25_search(query: str, items: list[dict], bm25: BM25Okapi, n: int) -> list[str]:
    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [items[i]["id"] for i in ranked[:n]]


def _vector_search(query: str, n: int, where: dict | None = None) -> list[str]:
    results = chroma_query(query, n_results=n, where=where)
    return [r["id"] for r in results]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def search(
    query: str,
    n: int = 10,
    formality_min: int | None = None,
    formality_max: int | None = None,
    category: str | None = None,
    season: str | None = None,
) -> HybridSearchResult:
    """
    Hybrid BM25 + vector search with RRF fusion.

    Optional filters are applied to the vector search (ChromaDB where clause)
    and post-filtered on the BM25 side.
    """
    items, bm25 = _load_corpus()
    pool_size = max(n * 3, 30)

    # ── BM25 ────────────────────────────────────────────────────────────────
    bm25_ids = _bm25_search(query, items, bm25, pool_size)

    # ── Vector ──────────────────────────────────────────────────────────────
    # ChromaDB requires $and for multiple conditions on the same field
    where: dict | None = None
    clauses = []
    if formality_min is not None:
        clauses.append({"formality": {"$gte": formality_min}})
    if formality_max is not None:
        clauses.append({"formality": {"$lte": formality_max}})
    if category:
        clauses.append({"category": {"$eq": category}})
    if len(clauses) == 1:
        where = clauses[0]
    elif len(clauses) > 1:
        where = {"$and": clauses}

    vector_ids = _vector_search(query, pool_size, where=where)

    # ── RRF fusion ──────────────────────────────────────────────────────────
    rrf_scores: dict[str, float] = {}
    for rank, item_id in enumerate(bm25_ids):
        rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + _rrf(rank)
    for rank, item_id in enumerate(vector_ids):
        rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + _rrf(rank)

    ranked_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    # ── Build item lookup ────────────────────────────────────────────────────
    item_map = {i["id"]: i for i in items}

    # ── Apply post-filters (BM25 side doesn't have metadata filtering) ──────
    filtered_ids = []
    for item_id in ranked_ids:
        item = item_map.get(item_id)
        if item is None:
            continue
        if formality_min is not None and item["formality"] < formality_min:
            continue
        if formality_max is not None and item["formality"] > formality_max:
            continue
        if category and item["category"] != category:
            continue
        if season:
            seasons = item.get("seasons", [])
            if isinstance(seasons, str):
                seasons = seasons.split(",")
            if season not in seasons:
                continue
        filtered_ids.append(item_id)
        if len(filtered_ids) >= n:
            break

    # ── Assemble result ──────────────────────────────────────────────────────
    top_score = rrf_scores.get(filtered_ids[0], 0.0) if filtered_ids else 0.0
    confidence = min(top_score / MAX_RRF, 1.0)

    hybrid_items = []
    for item_id in filtered_ids:
        raw = item_map[item_id]
        seasons_val = raw.get("seasons", [])
        if isinstance(seasons_val, str):
            seasons_val = seasons_val.split(",")
        occ_val = raw.get("occasions", [])
        if isinstance(occ_val, str):
            occ_val = occ_val.split(",")
        tags_val = raw.get("style_tags", [])
        if isinstance(tags_val, str):
            tags_val = tags_val.split(",")

        hybrid_items.append(HybridItem(
            item_id=item_id,
            name=raw.get("name", ""),
            category=raw.get("category", ""),
            subcategory=raw.get("subcategory", ""),
            color=raw.get("color", ""),
            color_family=raw.get("color_family", "neutral"),
            formality=int(raw.get("formality", 1)),
            occasions=occ_val,
            seasons=seasons_val,
            style_tags=tags_val,
            notes=raw.get("notes", ""),
            rrf_score=rrf_scores[item_id],
            metadata=raw,
        ))

    return HybridSearchResult(
        items=hybrid_items,
        confidence=confidence,
        query=query,
    )


def search_with_retry(
    query: str,
    formality_target: int,
    season: str | None = None,
    n: int = 10,
    confidence_threshold: float = 0.6,
) -> HybridSearchResult:
    """
    3-attempt retry loop used by OutfitAgent:
    1. Full context: exact formality, season filter
    2. Relax formality +-1
    3. Style-tags only (no formality filter)
    """
    # Attempt 1 — full context
    result = search(
        query=query,
        n=n,
        formality_min=formality_target,
        formality_max=formality_target,
        season=season,
    )
    if result.confidence >= confidence_threshold:
        return result

    # Attempt 2 — relax formality +-1
    result = search(
        query=query,
        n=n,
        formality_min=max(1, formality_target - 1),
        formality_max=min(5, formality_target + 1),
        season=season,
    )
    result.retry_count = 1
    if result.confidence >= confidence_threshold:
        return result

    # Attempt 3 — no formality filter, no season
    result = search(query=query, n=n)
    result.retry_count = 2
    return result
