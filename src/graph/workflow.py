"""
LangGraph workflow — wardrobe concierge state graph.

Topology:
  START -> resolve_context -> outfit_search -+-> occasion_reason -+-> manager_aggregate
                                             +-> gap_check        +
                                                         manager_aggregate -> hitl_gate
                                                                   (interrupt)
                                                                   approved? -> record_wear -> END
                                                                   declined? -> END

Fan-out: outfit_search has edges to BOTH occasion_reason and gap_check.
LangGraph waits for all incoming edges to a node before executing it (join semantics).

HITL: hitl_gate calls interrupt() which suspends the graph.
Resume via: graph.invoke(Command(resume={"approved": True}), config=...)
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.models.graph_state import GraphState
from src.graph.nodes import (
    resolve_context,
    outfit_search,
    occasion_reason,
    gap_check,
    manager_aggregate,
    hitl_gate,
    record_wear,
)

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def _route_after_hitl(state: GraphState) -> str:
    return "record_wear" if state.get("human_approved") else END


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
def build_graph(checkpointer=None):
    """
    Build and compile the wardrobe concierge graph.

    Args:
        checkpointer: LangGraph checkpointer for persistence.
                      Defaults to in-memory MemorySaver.

    Returns:
        Compiled LangGraph graph.
    """
    workflow = StateGraph(GraphState)

    # Nodes
    workflow.add_node("resolve_context",   resolve_context)
    workflow.add_node("outfit_search",     outfit_search)
    workflow.add_node("occasion_reason",   occasion_reason)
    workflow.add_node("gap_check",         gap_check)
    workflow.add_node("manager_aggregate", manager_aggregate)
    workflow.add_node("hitl_gate",         hitl_gate)
    workflow.add_node("record_wear",       record_wear)

    # Edges
    workflow.add_edge(START,              "resolve_context")
    workflow.add_edge("resolve_context",  "outfit_search")

    # Fan-out from outfit_search to two parallel branches
    workflow.add_edge("outfit_search",    "occasion_reason")
    workflow.add_edge("outfit_search",    "gap_check")

    # Join at manager_aggregate
    workflow.add_edge("occasion_reason",  "manager_aggregate")
    workflow.add_edge("gap_check",        "manager_aggregate")

    # HITL
    workflow.add_edge("manager_aggregate", "hitl_gate")
    workflow.add_conditional_edges("hitl_gate", _route_after_hitl)
    workflow.add_edge("record_wear", END)

    cp = checkpointer or MemorySaver()
    return workflow.compile(checkpointer=cp)


# Module-level compiled graph (shared across requests)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
