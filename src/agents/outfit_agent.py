"""
Outfit Agent — worker model (claude-haiku).

Builds a complete outfit from the wardrobe using:
  1. Hybrid search (BM25 + vector, RRF k=60) with 3-attempt retry loop
  2. Graph context: PAIRS_WITH neighbors + WORN_TOGETHER history for top hit
  3. LLM selects final items with per-item reasoning

Returns OutfitResult in state.
"""

from __future__ import annotations

import json
import os
import re

from src.models.graph_state import GraphState
from src.models.schemas import OutfitItem, OutfitResult
from src.retrieval.hybrid_search import search_with_retry
from src.retrieval.graph_retrieval import get_pairs_for_item, get_worn_together
from src.llm.client import chat
from src.llm.router import get_model


# ---------------------------------------------------------------------------
# Graph context helpers
# ---------------------------------------------------------------------------
def _build_graph_context(top_item_id: str) -> str:
    lines: list[str] = []
    try:
        pairs = get_pairs_for_item(top_item_id, limit=8)
        if pairs:
            names = ", ".join(f"{p.name} ({p.category})" for p in pairs[:5])
            lines.append(f"Items known to pair well with {top_item_id}: {names}")
    except Exception:
        pass
    try:
        worn = get_worn_together(top_item_id, limit=5)
        if worn:
            names = ", ".join(f"{w.name}" for w in worn[:3])
            lines.append(f"Previously worn together with {top_item_id}: {names}")
    except Exception:
        pass
    return "\n".join(lines) if lines else "No graph context available."


# ---------------------------------------------------------------------------
# LLM outfit selection
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a personal stylist building a complete outfit from a wardrobe.
Select one item per category where possible (top, bottom, shoes, accessories).
If a dress is selected (subcategory="dress"), do NOT also select a separate bottom — the dress covers both.
Consider color coordination, formality alignment, the occasion, and the user's style profile.
Respond ONLY with valid JSON — no markdown, no extra text."""


def _build_user_prompt(
    resolved: dict,
    candidates: list[dict],
    graph_context: str,
) -> str:
    occasion      = resolved.get("occasion", "")
    formality     = resolved.get("formality_target", 3)
    season        = resolved.get("season", "")
    weather       = resolved.get("weather_summary", "")
    prefs         = ", ".join(resolved.get("style_preferences", [])) or "none"
    avoid         = resolved.get("avoid_items", [])
    style_profile = resolved.get("style_profile", {})
    gender        = style_profile.get("gender", "")
    style_notes   = style_profile.get("style_notes", "")
    fit_prefs     = ", ".join(style_profile.get("fit_preferences", [])) or "none"
    colour_prefs  = ", ".join(style_profile.get("colour_preferences", [])) or "none"
    avoid_styles  = ", ".join(style_profile.get("avoid_styles", [])) or "none"

    candidate_lines = []
    for c in candidates:
        tags = c.get("style_tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        occ = c.get("occasions", [])
        if isinstance(occ, list):
            occ = ", ".join(occ)
        candidate_lines.append(
            f'  {c["item_id"]} | {c["name"]:35s} | {c["category"]:12s} | '
            f'formality={c["formality"]} | color={c["color"]} | tags={tags}'
        )

    avoid_str = ", ".join(avoid) if avoid else "none"

    profile_lines = []
    if gender:
        profile_lines.append(f"GENDER: {gender}")
    if style_notes:
        profile_lines.append(f"STYLE NOTES: {style_notes}")
    if fit_prefs != "none":
        profile_lines.append(f"FIT PREFERENCES: {fit_prefs}")
    if colour_prefs != "none":
        profile_lines.append(f"COLOUR PREFERENCES: {colour_prefs}")
    if avoid_styles != "none":
        profile_lines.append(f"STYLES TO AVOID: {avoid_styles}")
    profile_block = "\n".join(profile_lines) if profile_lines else "No profile set."

    return f"""Build a complete outfit for this occasion.

OCCASION: {occasion}
FORMALITY TARGET: {formality}/5
SEASON: {season}
WEATHER: {weather}
STYLE PREFERENCES: {prefs}
ITEMS TO AVOID (worn recently): {avoid_str}

USER STYLE PROFILE:
{profile_block}

CANDIDATE ITEMS:
{chr(10).join(candidate_lines)}

GRAPH CONTEXT:
{graph_context}

Select items to form a complete outfit (top, bottom, shoes, + optional accessories).
Respect the user's style profile above all else — gender, fit preferences, and style notes must guide selection.
If a dress is chosen, do not also pick a separate bottom.
Prioritize formality {formality} items. Match colors. Avoid the listed items.

Respond in this exact JSON format:
{{
  "items": [
    {{"item_id": "item_XXX", "name": "...", "category": "...", "subcategory": "...", "color": "...", "formality": N, "reason": "one sentence why this works"}},
    ...
  ],
  "confidence": 0.0
}}"""


def _parse_llm_response(content: str, candidates: list[dict]) -> tuple[list[OutfitItem], float]:
    """Parse LLM JSON response; fall back to top search hits if parsing fails."""
    # Strip markdown fences if present
    content = re.sub(r"```(?:json)?", "", content).strip()
    try:
        data = json.loads(content)
        items = [OutfitItem(**i) for i in data.get("items", [])]
        confidence = float(data.get("confidence", 0.7))
        if items:
            return items, confidence
    except Exception:
        pass

    # Fallback: use top search candidates, one per category
    seen_cats: set[str] = set()
    fallback_items: list[OutfitItem] = []
    for c in candidates:
        cat = c.get("category", "")
        if cat not in seen_cats:
            seen_cats.add(cat)
            fallback_items.append(OutfitItem(
                item_id=c["item_id"],
                name=c["name"],
                category=cat,
                subcategory=c.get("subcategory", ""),
                color=c.get("color", ""),
                formality=int(c.get("formality", 3)),
                reason="Selected from top wardrobe matches.",
            ))
    return fallback_items, 0.5


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run(state: GraphState) -> dict:
    resolved     = state.get("resolved_context", {})
    occasion     = resolved.get("occasion", "")
    formality    = resolved.get("formality_target", 3)
    season       = resolved.get("season")
    raw_query    = state.get("raw_query", occasion)

    # 1. Hybrid search with retry
    search_result = search_with_retry(
        query=f"{raw_query} {occasion}",
        formality_target=formality,
        season=season,
        n=15,
    )

    candidates = [
        {
            "item_id":    item.item_id,
            "name":       item.name,
            "category":   item.category,
            "subcategory": item.subcategory,
            "color":      item.color,
            "color_family": item.color_family,
            "formality":  item.formality,
            "occasions":  item.occasions,
            "style_tags": item.style_tags,
        }
        for item in search_result.items
    ]

    # 2. Graph context for top result
    graph_context = ""
    if candidates:
        graph_context = _build_graph_context(candidates[0]["item_id"])

    # 3. LLM selects outfit
    prompt = _build_user_prompt(resolved, candidates, graph_context)
    raw_content = chat(
        model=get_model("outfit"),
        system=SYSTEM_PROMPT,
        user=prompt,
        max_tokens=1024,
        role="outfit",
    )

    items, llm_confidence = _parse_llm_response(raw_content, candidates)

    # Blend search confidence with LLM confidence
    final_confidence = round((search_result.confidence + llm_confidence) / 2, 3)

    result = OutfitResult(
        items=items,
        confidence=final_confidence,
        retry_count=search_result.retry_count,
        search_query_used=search_result.query,
    )

    return {"outfit_result": result.model_dump()}
