"""
Occasion Reasoner Agent — worker model (claude-haiku).

Validates the proposed outfit against the occasion:
  - Formality alignment (all items within +-1 of target)
  - Weather mismatches (e.g. suede shoes + rain, sandals + cold)
  - Repeat wear (same item worn for same occasion within 30 days)

Returns OccasionResult in state.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta

import anthropic

from src.models.graph_state import GraphState
from src.models.schemas import OccasionResult

WORKER_MODEL = os.getenv("WORKER_MODEL", "claude-haiku-4-5-20251001")
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# ---------------------------------------------------------------------------
# Repeat-wear check (pure logic, no LLM needed)
# ---------------------------------------------------------------------------
def _check_repeat_wear(
    item_ids: list[str],
    occasion: str,
    memory: dict,
    lookback_days: int = 30,
) -> tuple[bool, list[str]]:
    """
    Returns (flag, list_of_repeated_item_ids).
    True if any item was worn for the same occasion within lookback_days.
    """
    cutoff = datetime.now() - timedelta(days=lookback_days)
    repeated: list[str] = []

    for entry in memory.get("recent_wear", []):
        if entry.get("occasion") != occasion:
            continue
        try:
            worn_on = datetime.strptime(entry["worn_on"], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        if worn_on < cutoff:
            continue
        for item_id in item_ids:
            if item_id in entry.get("item_ids", []) and item_id not in repeated:
                repeated.append(item_id)

    return len(repeated) > 0, repeated


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a personal stylist reviewing an outfit for occasion appropriateness.
Be concise and practical. Respond ONLY with valid JSON — no markdown, no extra text."""


def _build_prompt(resolved: dict, outfit_items: list[dict], repeat_items: list[str]) -> str:
    occasion  = resolved.get("occasion", "")
    formality = resolved.get("formality_target", 3)
    weather   = resolved.get("weather_summary", "")

    item_lines = []
    for item in outfit_items:
        item_lines.append(
            f'  {item.get("item_id")} | {item.get("name"):35s} | '
            f'category={item.get("category"):12s} | formality={item.get("formality")} | '
            f'subcategory={item.get("subcategory", "")}'
        )

    repeat_note = ""
    if repeat_items:
        repeat_note = f"\nNOTE: These items were recently worn for the same occasion: {', '.join(repeat_items)}"

    return f"""Review this outfit for occasion appropriateness.

OCCASION: {occasion}
FORMALITY TARGET: {formality}/5
WEATHER: {weather}{repeat_note}

PROPOSED OUTFIT:
{chr(10).join(item_lines)}

Check:
1. FORMALITY: Are all items within +-1 of formality {formality}? Any mismatches?
2. WEATHER: Any weather-related issues? (suede in rain, sandals in cold, heavy coat in heat)
3. REPEAT WEAR: Items worn recently for same occasion are flagged above if any.

Respond in this exact JSON format:
{{
  "approved": true,
  "confidence": 0.85,
  "formality_ok": true,
  "weather_ok": true,
  "repeat_wear_flag": false,
  "suggestions": [],
  "notes": "brief summary"
}}"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run(state: GraphState) -> dict:
    resolved   = state.get("resolved_context", {})
    outfit_res = state.get("outfit_result", {})
    memory     = state.get("user_memory", {})

    items_data = outfit_res.get("items", [])
    item_ids   = [i.get("item_id") for i in items_data]
    occasion   = resolved.get("occasion", "")

    # Repeat-wear check (deterministic, no LLM)
    repeat_flag, repeated_ids = _check_repeat_wear(item_ids, occasion, memory)

    # LLM validation
    prompt = _build_prompt(resolved, items_data, repeated_ids)
    response = _get_client().messages.create(
        model=WORKER_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    try:
        data = json.loads(raw)
        result = OccasionResult(
            approved=bool(data.get("approved", True)),
            confidence=float(data.get("confidence", 0.8)),
            formality_ok=bool(data.get("formality_ok", True)),
            weather_ok=bool(data.get("weather_ok", True)),
            repeat_wear_flag=bool(data.get("repeat_wear_flag", repeat_flag)),
            suggestions=data.get("suggestions", []),
            notes=data.get("notes", ""),
        )
    except Exception:
        result = OccasionResult(
            approved=True,
            confidence=0.7,
            formality_ok=True,
            weather_ok=True,
            repeat_wear_flag=repeat_flag,
            suggestions=[],
            notes="Validation parsing error — defaulting to approved.",
        )

    return {"occasion_result": result.model_dump()}
