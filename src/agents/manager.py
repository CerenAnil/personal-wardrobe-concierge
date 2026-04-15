"""
Manager Agent — resolve() and aggregate().

resolve():
  Reads occasion + optional context, calls weather API, loads user memory,
  infers formality + season, returns ResolvedContext in state.

aggregate():
  Combines outfit_result + occasion_result + gap_result, checks palette
  coherence via Neo4j graph, builds FinalOutfit in state.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Optional

from src.models.graph_state import GraphState
from src.models.schemas import FinalOutfit, OutfitItem, ResolvedContext
from src.memory import user_memory
from src.mcp.weather_server import get_weather
from src.retrieval.graph_retrieval import check_palette_coherence

# ---------------------------------------------------------------------------
# Formality inference
# ---------------------------------------------------------------------------
OCCASION_FORMALITY: dict[str, int] = {
    "gym":          1,
    "casual":       2,
    "weekend":      2,
    "beach":        2,
    "smart-casual": 3,
    "smart_casual": 3,
    "work":         3,
    "dinner":       3,
    "date-night":   3,
    "job-interview":    4,
    "job_interview":    4,
    "wedding-guest":    4,
    "wedding_guest":    4,
    "formal":       4,
    "black-tie":    5,
    "black_tie":    5,
}

DRESS_CODE_OVERRIDE: dict[str, int] = {
    "casual":        2,
    "smart casual":  3,
    "business casual": 3,
    "smart":         3,
    "formal":        4,
    "black tie optional": 4,
    "black tie":     5,
}


def _infer_formality(occasion: str, dress_code: Optional[str]) -> int:
    if dress_code:
        for key, val in DRESS_CODE_OVERRIDE.items():
            if key in dress_code.lower():
                return val
    return OCCASION_FORMALITY.get(occasion.lower().replace(" ", "-"), 3)


def _infer_season(date_str: Optional[str]) -> str:
    if not date_str:
        month = datetime.now().month
    else:
        try:
            month = datetime.strptime(date_str, "%Y-%m-%d").month
        except ValueError:
            month = datetime.now().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


# ---------------------------------------------------------------------------
# resolve()
# ---------------------------------------------------------------------------
def resolve(state: GraphState) -> dict:
    """
    Enriches raw query with weather, memory, and inferred context.
    Returns state updates: resolved_context, user_memory.
    """
    user_id  = state.get("user_id", "user_001")
    city     = state.get("city") or ""
    occasion = _parse_occasion(state.get("raw_query", ""))
    dress_code = state.get("dress_code")
    today    = datetime.now().strftime("%Y-%m-%d")

    # Weather
    weather: dict = {}
    if city:
        weather = get_weather(city, today)
        if "error" in weather:
            weather = {"summary": f"weather unavailable for {city}", "condition": "unknown"}
    weather_summary = weather.get("summary", "weather not available")

    # Season — infer from current date
    season = _infer_season(today)

    # Formality
    formality = _infer_formality(occasion, dress_code)

    # Memory
    memory = user_memory.load(user_id)
    avoid_items  = user_memory.get_avoid_items(memory, occasion)
    style_profile = user_memory.get_style_profile(memory)

    # Allow per-request style_profile override (passed in state by API)
    if state.get("style_profile"):
        style_profile = {**style_profile, **state["style_profile"]}

    resolved = ResolvedContext(
        occasion=occasion,
        formality_target=formality,
        season=season,
        weather_summary=weather_summary,
        city=city or None,
        dress_code=dress_code,
        who_with=state.get("who_with"),
        style_preferences=memory.get("style_preferences", []),
        avoid_items=avoid_items,
        style_profile=style_profile,
    )

    return {
        "resolved_context": resolved.model_dump(),
        "user_memory": memory,
    }


def _parse_occasion(raw_query: str) -> str:
    """Best-effort occasion extraction from raw query string."""
    q = raw_query.lower()
    for key in sorted(OCCASION_FORMALITY, key=len, reverse=True):
        if key.replace("-", " ") in q or key.replace("_", " ") in q:
            return key
    # fallback: first word or "casual"
    first = raw_query.strip().split()[0].lower() if raw_query.strip() else "casual"
    return OCCASION_FORMALITY.get(first, None) and first or "casual"


# ---------------------------------------------------------------------------
# aggregate()
# ---------------------------------------------------------------------------
def aggregate(state: GraphState) -> dict:
    """
    Merges outfit_result + occasion_result + gap_result into a FinalOutfit.
    Runs a palette coherence check via the graph.
    """
    resolved     = state.get("resolved_context", {})
    outfit_res   = state.get("outfit_result", {})
    occasion_res = state.get("occasion_result", {})
    gap_res      = state.get("gap_result", {})

    items_data: list[dict] = outfit_res.get("items", [])
    items = [OutfitItem(**i) for i in items_data]

    # Palette coherence via Neo4j (best-effort — skip if graph unavailable)
    palette_label = "unknown"
    if items:
        try:
            coherence = check_palette_coherence([i.item_id for i in items])
            palette_label = coherence.dominant_palette
            if not coherence.is_coherent:
                palette_label += " (mixed)"
        except Exception:
            pass

    outfit_id = f"outfit_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

    occasion_notes = occasion_res.get("notes", "")
    if not occasion_res.get("approved", True):
        suggestions = occasion_res.get("suggestions", [])
        if suggestions:
            occasion_notes = "Suggestions: " + "; ".join(suggestions)

    ready = (
        occasion_res.get("approved", True)
        and gap_res.get("complete", True)
    )

    final = FinalOutfit(
        outfit_id=outfit_id,
        occasion=resolved.get("occasion", ""),
        items=items,
        weather_summary=resolved.get("weather_summary", ""),
        occasion_notes=occasion_notes,
        gap_message=gap_res.get("message", ""),
        color_palette=palette_label,
        ready_to_wear=ready,
    )

    return {
        "final_outfit": final.model_dump(),
        "awaiting_human_approval": True,
    }
