"""
LangGraph node wrappers with error guards.

Each node catches exceptions and writes to state["error"] rather than crashing
the graph, so the HITL gate always has something to present to the user.
"""

from __future__ import annotations

import traceback

from src.models.graph_state import GraphState
from src.agents import manager, outfit_agent, occasion_agent, gap_agent
from src.memory import user_memory as memory_store


# ---------------------------------------------------------------------------
# Node: resolve_context
# ---------------------------------------------------------------------------
def resolve_context(state: GraphState) -> dict:
    try:
        return manager.resolve(state)
    except Exception as e:
        return {"error": f"resolve_context failed: {e}\n{traceback.format_exc()}"}


# ---------------------------------------------------------------------------
# Node: outfit_search
# ---------------------------------------------------------------------------
def outfit_search(state: GraphState) -> dict:
    if state.get("error"):
        return {}
    try:
        return outfit_agent.run(state)
    except Exception as e:
        return {"error": f"outfit_search failed: {e}\n{traceback.format_exc()}"}


# ---------------------------------------------------------------------------
# Node: occasion_reason  (parallel branch 1)
# ---------------------------------------------------------------------------
def occasion_reason(state: GraphState) -> dict:
    if state.get("error") or not state.get("outfit_result"):
        return {"occasion_result": {
            "approved": True, "confidence": 0.0,
            "formality_ok": True, "weather_ok": True,
            "repeat_wear_flag": False, "suggestions": [], "notes": "skipped",
        }}
    try:
        return occasion_agent.run(state)
    except Exception as e:
        return {"occasion_result": {
            "approved": True, "confidence": 0.0,
            "formality_ok": True, "weather_ok": True,
            "repeat_wear_flag": False, "suggestions": [],
            "notes": f"occasion check error: {e}",
        }}


# ---------------------------------------------------------------------------
# Node: gap_check  (parallel branch 2)
# ---------------------------------------------------------------------------
def gap_check(state: GraphState) -> dict:
    if state.get("error") or not state.get("outfit_result"):
        return {"gap_result": {
            "complete": True, "missing_categories": [], "gap_queries": [], "message": "skipped",
        }}
    try:
        return gap_agent.run(state)
    except Exception as e:
        return {"gap_result": {
            "complete": True, "missing_categories": [], "gap_queries": [],
            "message": f"gap check error: {e}",
        }}


# ---------------------------------------------------------------------------
# Node: manager_aggregate
# ---------------------------------------------------------------------------
def manager_aggregate(state: GraphState) -> dict:
    if state.get("error"):
        return {"final_outfit": None, "awaiting_human_approval": False}
    try:
        return manager.aggregate(state)
    except Exception as e:
        return {
            "error": f"manager_aggregate failed: {e}\n{traceback.format_exc()}",
            "final_outfit": None,
            "awaiting_human_approval": False,
        }


# ---------------------------------------------------------------------------
# Node: hitl_gate   — uses LangGraph interrupt()
# ---------------------------------------------------------------------------
def hitl_gate(state: GraphState) -> dict:
    from langgraph.types import interrupt

    final_outfit = state.get("final_outfit")
    error        = state.get("error")

    # Suspend and surface the outfit (or error) to the caller
    response = interrupt({
        "final_outfit": final_outfit,
        "error":        error,
        "message":      "Review the outfit. Respond with {approved: true/false}.",
    })

    approved = bool((response or {}).get("approved", False))
    return {
        "human_approved":          approved,
        "awaiting_human_approval": False,
    }


# ---------------------------------------------------------------------------
# Node: record_wear
# ---------------------------------------------------------------------------
def record_wear(state: GraphState) -> dict:
    """
    Writes approved outfit to wear_log + Neo4j WORN_TOGETHER edges.
    Requires WEAR_SECRET (injected here, never exposed to agents).
    """
    import os
    from datetime import datetime
    from src.mcp.wardrobe_server import log_outfit
    from src.db.neo4j_client import run_write

    final_outfit = state.get("final_outfit", {})
    user_id      = state.get("user_id", "user_001")
    resolved     = state.get("resolved_context", {})

    outfit_id       = final_outfit.get("outfit_id", "")
    item_ids        = [i["item_id"] for i in final_outfit.get("items", [])]
    occasion        = final_outfit.get("occasion", "")
    weather_summary = final_outfit.get("weather_summary", "")
    worn_on         = datetime.now().strftime("%Y-%m-%d")
    wear_secret     = os.getenv("WEAR_SECRET", "")

    # Write wear log via wardrobe MCP tool (secret-gated)
    log_result = log_outfit(
        outfit_id=outfit_id,
        item_ids=item_ids,
        occasion=occasion,
        worn_on=worn_on,
        weather_summary=weather_summary,
        context_json=str(resolved),
        secret=wear_secret,
    )

    # Update Neo4j WORN_TOGETHER edges
    if item_ids and "error" not in log_result:
        try:
            for i, id_a in enumerate(item_ids):
                for id_b in item_ids[i + 1:]:
                    run_write(
                        """
                        MATCH (a:Item {id: $id_a}), (b:Item {id: $id_b})
                        MERGE (a)-[:WORN_TOGETHER]->(b)
                        """,
                        {"id_a": id_a, "id_b": id_b},
                    )
        except Exception:
            pass  # Graph update is best-effort; SQLite wear log is source of truth

    # Update user memory
    memory_store.update_after_session(
        user_id=user_id,
        outfit_id=outfit_id,
        occasion=occasion,
        item_ids=item_ids,
        worn_on=worn_on,
    )

    return {"human_approved": True}
