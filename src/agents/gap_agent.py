"""
Gap Agent — worker model (no LLM needed, pure logic).

Calls gap_finder_server.find_gaps() with the proposed outfit,
formats the result into a GapResult, and passes it to manager_aggregate.
"""

from __future__ import annotations

from src.models.graph_state import GraphState
from src.models.schemas import GapResult
from src.mcp.gap_finder_server import find_gaps


def run(state: GraphState) -> dict:
    resolved   = state.get("resolved_context", {})
    outfit_res = state.get("outfit_result", {})

    occasion  = resolved.get("occasion", "casual")
    formality = resolved.get("formality_target", 3)

    # Build outfit list with the fields find_gaps needs
    proposed = [
        {
            "category":    item.get("category", ""),
            "subcategory": item.get("subcategory", ""),
            "color_family": item.get("color_family", "neutral"),
            "style_tags":  item.get("style_tags", []),
        }
        for item in outfit_res.get("items", [])
    ]

    raw = find_gaps(proposed, occasion, formality)

    result = GapResult(
        complete=bool(raw.get("complete", True)),
        missing_categories=raw.get("missing_categories", []),
        gap_queries=raw.get("gap_queries", []),
        message=raw.get("message", ""),
    )

    return {"gap_result": result.model_dump()}
