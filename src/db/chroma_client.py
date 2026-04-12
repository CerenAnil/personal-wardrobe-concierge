"""
ChromaDB client — vector store for wardrobe items.

Document format (same text fed to BM25 + ChromaDB):
  "{name} {subcategory} {color} {material} {occasions} {style_tags} {notes}"

Metadata values must be str / int / float — lists stored as comma-separated strings.
"""

from __future__ import annotations

import os
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR   = os.getenv("CHROMA_PERSIST_DIR", ".cache/chroma")
COLLECTION   = "wardrobe_items"
EMBED_MODEL  = "all-MiniLM-L6-v2"


def _client() -> chromadb.PersistentClient:
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def _embed_fn():
    return SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)


def get_collection():
    return _client().get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------
def _item_to_document(item: dict) -> str:
    """Build the text fed to both BM25 and ChromaDB embeddings."""
    parts = [
        item.get("name", ""),
        item.get("subcategory", ""),
        item.get("color", ""),
        item.get("material", ""),
        _list_field(item, "occasions"),
        _list_field(item, "style_tags"),
        item.get("notes", ""),
    ]
    return " ".join(p for p in parts if p)


def _item_to_metadata(item: dict) -> dict:
    """Flatten item to ChromaDB-safe metadata (str / int / float only)."""
    return {
        "name":         item.get("name", ""),
        "category":     item.get("category", ""),
        "subcategory":  item.get("subcategory", ""),
        "color":        item.get("color", ""),
        "color_family": item.get("color_family", ""),
        "material":     item.get("material", ""),
        "formality":    int(item.get("formality", 0)),
        "occasions":    _list_to_str(item, "occasions"),
        "seasons":      _list_to_str(item, "seasons"),
        "style_tags":   _list_to_str(item, "style_tags"),
        "owned_since":  item.get("owned_since") or "",
        "last_worn":    item.get("last_worn") or "",
        "notes":        item.get("notes") or "",
    }


def _list_field(item: dict, key: str) -> str:
    val = item.get(key, [])
    if isinstance(val, list):
        return " ".join(val)
    return str(val)


def _list_to_str(item: dict, key: str) -> str:
    val = item.get(key, [])
    if isinstance(val, list):
        return ",".join(val)
    return str(val)


# ---------------------------------------------------------------------------
# Upsert / query
# ---------------------------------------------------------------------------
def upsert_items(items: list[dict]) -> None:
    col = get_collection()
    col.upsert(
        ids=[i["id"] for i in items],
        documents=[_item_to_document(i) for i in items],
        metadatas=[_item_to_metadata(i) for i in items],
    )


def query_items(
    query_text: str,
    n_results: int = 10,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Returns list of dicts with keys: id, document, metadata, distance.
    Lower distance = better match (cosine space).
    """
    col = get_collection()
    kwargs: dict = {"query_texts": [query_text], "n_results": n_results}
    if where:
        kwargs["where"] = where

    results = col.query(**kwargs)
    output = []
    for i, item_id in enumerate(results["ids"][0]):
        output.append({
            "id":       item_id,
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return output


def reset_collection() -> None:
    client = _client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def count() -> int:
    return get_collection().count()
