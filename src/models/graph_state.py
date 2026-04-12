"""
LangGraph state TypedDict for the wardrobe workflow.

All agent output fields are dicts (serialised Pydantic) — not Pydantic objects —
so LangGraph checkpointing works without a custom serialiser.
"""

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict


class GraphState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────────────────
    user_id: str
    raw_query: str           # raw occasion description from user
    session_id: str          # used as LangGraph thread_id
    city: Optional[str]
    dress_code: Optional[str]
    who_with: Optional[str]

    # ── Resolved context (after resolve_context node) ────────────────────────
    resolved_context: Optional[dict]   # ResolvedContext.model_dump()
    user_memory: Optional[dict]        # UserMemory.model_dump()

    # ── Agent outputs (fan-out parallel nodes) ───────────────────────────────
    outfit_result: Optional[dict]      # OutfitResult.model_dump()
    occasion_result: Optional[dict]    # OccasionResult.model_dump()
    gap_result: Optional[dict]         # GapResult.model_dump()

    # ── Final assembly ───────────────────────────────────────────────────────
    final_outfit: Optional[dict]       # FinalOutfit.model_dump()

    # ── HITL gate ────────────────────────────────────────────────────────────
    awaiting_human_approval: bool
    human_approved: bool

    # ── Control ──────────────────────────────────────────────────────────────
    retry_count: int
    error: Optional[str]
