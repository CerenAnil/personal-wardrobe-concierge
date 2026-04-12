"""
Per-user JSON memory store.

File: data/memory/{user_id}.json

Tracks style preferences, recent wear history, and per-occasion item history.
Used by resolve_context to populate ResolvedContext.avoid_items and style_preferences.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional

MEMORY_DIR = os.getenv("MEMORY_STORE_PATH", "data/memory")

DEFAULT_MEMORY = {
    "user_id": "user_001",
    "style_preferences": ["minimal", "classic", "neutral-palette"],
    "avoid_styles": [],
    "recent_wear": [],       # list of {outfit_id, occasion, item_ids, worn_on}
    "occasion_history": {},  # {occasion: [item_ids used]}
    "total_sessions": 0,
}


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------
def _path(user_id: str) -> str:
    return os.path.join(MEMORY_DIR, f"{user_id}.json")


def load(user_id: str) -> dict:
    """Load user memory, creating a default file if it doesn't exist."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    p = _path(user_id)
    if not os.path.exists(p):
        mem = {**DEFAULT_MEMORY, "user_id": user_id}
        _save(user_id, mem)
        return mem
    with open(p) as f:
        return json.load(f)


def _save(user_id: str, memory: dict) -> None:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(_path(user_id), "w") as f:
        json.dump(memory, f, indent=2)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def get_avoid_items(memory: dict, occasion: str, lookback_days: int = 30) -> list[str]:
    """
    Return item_ids worn for this occasion within the last `lookback_days` days.
    These are passed to ResolvedContext.avoid_items so agents skip repeat-wear.
    """
    cutoff = datetime.now() - timedelta(days=lookback_days)
    avoid: list[str] = []
    for entry in memory.get("recent_wear", []):
        if entry.get("occasion") != occasion:
            continue
        try:
            worn_on = datetime.strptime(entry["worn_on"], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        if worn_on >= cutoff:
            avoid.extend(entry.get("item_ids", []))
    return list(set(avoid))


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------
def update_after_session(
    user_id: str,
    outfit_id: str,
    occasion: str,
    item_ids: list[str],
    worn_on: str,
) -> None:
    """
    Called by record_wear node after HITL approval.
    Appends to recent_wear, updates occasion_history, increments total_sessions.
    Trims recent_wear to last 50 entries.
    """
    memory = load(user_id)

    entry = {
        "outfit_id": outfit_id,
        "occasion":  occasion,
        "item_ids":  item_ids,
        "worn_on":   worn_on,
    }
    memory["recent_wear"].append(entry)
    memory["recent_wear"] = memory["recent_wear"][-50:]

    history = memory.setdefault("occasion_history", {})
    existing = set(history.get(occasion, []))
    existing.update(item_ids)
    history[occasion] = list(existing)

    memory["total_sessions"] = memory.get("total_sessions", 0) + 1

    _save(user_id, memory)


def update_preferences(user_id: str, style_preferences: list[str]) -> None:
    memory = load(user_id)
    memory["style_preferences"] = style_preferences
    _save(user_id, memory)
