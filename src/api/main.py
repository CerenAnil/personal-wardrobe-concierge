"""
FastAPI server — Personal Wardrobe Concierge

Endpoints:
  POST /outfit           Start a wardrobe query (runs graph to HITL interrupt)
  POST /approve          Resume after HITL (approve or decline outfit)
  GET  /memory/{user_id} Return user memory JSON
  DELETE /memory/{user_id} Clear user memory
  GET  /health           Health check

The graph uses MemorySaver (in-process) so the HITL state persists between
POST /outfit and POST /approve within the same server lifetime.
"""

from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langgraph.types import Command

from dotenv import load_dotenv
load_dotenv(override=True)

from src.graph.workflow import get_graph
from src.memory import user_memory as memory_store
from src.llm import router as llm_router
from src.llm import history as llm_history

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Wardrobe Concierge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class OutfitRequest(BaseModel):
    raw_query: str
    user_id: str = "user_001"
    session_id: Optional[str] = None
    city: Optional[str] = None
    dress_code: Optional[str] = None
    who_with: Optional[str] = None
    style_profile: Optional[dict] = None  # overrides persisted profile for this request


class StyleProfileRequest(BaseModel):
    gender: Optional[str] = None
    style_notes: Optional[str] = None
    fit_preferences: Optional[list[str]] = None
    colour_preferences: Optional[list[str]] = None
    avoid_styles: Optional[list[str]] = None


class ApprovalRequest(BaseModel):
    session_id: str
    approved: bool


class SettingsRequest(BaseModel):
    outfit_model: Optional[str] = None
    occasion_model: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "wardrobe-concierge"}


@app.post("/outfit")
def request_outfit(req: OutfitRequest):
    """
    Start a wardrobe query. Runs the LangGraph workflow up to the HITL interrupt.

    Returns:
      - status: "awaiting_approval" + outfit data, or
      - status: "error" if the graph failed before producing an outfit
    """
    graph = get_graph()
    session_id = req.session_id or uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "user_id":       req.user_id,
        "raw_query":     req.raw_query,
        "session_id":    session_id,
        "city":          req.city or "",
        "dress_code":    req.dress_code,
        "who_with":      req.who_with,
        "style_profile": req.style_profile,   # None if not provided
        "retry_count":   0,
    }

    try:
        result = graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        # Graph completed without interrupt (shouldn't happen in normal flow)
        return {
            "session_id": session_id,
            "status": "complete",
            "outfit": result.get("final_outfit"),
        }

    interrupt_val = interrupts[0].value
    outfit  = interrupt_val.get("final_outfit")
    error   = interrupt_val.get("error")

    if error and not outfit:
        return {
            "session_id": session_id,
            "status": "error",
            "error": error,
            "outfit": None,
        }

    return {
        "session_id": session_id,
        "status": "awaiting_approval",
        "outfit": outfit,
        "error": error,         # surface non-fatal errors (e.g. Neo4j down)
    }


@app.post("/approve")
def approve_outfit(req: ApprovalRequest):
    """
    Resume the HITL-suspended graph.

    approved=True  -> record_wear -> memory + wear_log updated
    approved=False -> graph ends, nothing recorded
    """
    graph = get_graph()
    config = {"configurable": {"thread_id": req.session_id}}

    try:
        result = graph.invoke(
            Command(resume={"approved": req.approved}),
            config=config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "session_id":    req.session_id,
        "status":        "logged" if req.approved else "declined",
        "human_approved": result.get("human_approved", req.approved),
    }


@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    return memory_store.load(user_id)


@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    """Return the style_profile for a user."""
    mem = memory_store.load(user_id)
    return memory_store.get_style_profile(mem)


@app.put("/profile/{user_id}")
def update_profile(user_id: str, req: StyleProfileRequest):
    """
    Update persisted style_profile for a user.
    Merges the provided fields into the existing profile.
    """
    patch = req.model_dump(exclude_none=True)
    updated = memory_store.update_style_profile(user_id, patch)
    return {"user_id": user_id, "style_profile": updated}


@app.delete("/memory/{user_id}")
def reset_memory(user_id: str):
    mem_path = os.path.join(
        os.getenv("MEMORY_STORE_PATH", "data/memory"),
        f"{user_id}.json",
    )
    if os.path.exists(mem_path):
        os.remove(mem_path)
    return {"status": "cleared", "user_id": user_id}


# ---------------------------------------------------------------------------
# Settings — runtime model routing
# ---------------------------------------------------------------------------
@app.get("/settings")
def get_settings():
    """Return current model routing config."""
    return {
        "routing": llm_router.describe_routing(),
        "options": {
            "cloud": "claude-haiku-4-5-20251001",
            "local": "qwen/qwen3.5-9b",
        },
    }


@app.put("/settings")
def update_settings(req: SettingsRequest):
    """Override model routing at runtime (no server restart needed)."""
    if req.outfit_model is not None:
        llm_router.set_model("outfit", req.outfit_model)
    if req.occasion_model is not None:
        llm_router.set_model("occasion", req.occasion_model)
    return {"routing": llm_router.describe_routing()}


# ---------------------------------------------------------------------------
# LLM history
# ---------------------------------------------------------------------------
@app.get("/llm-history")
def get_llm_history():
    """Return all logged LLM calls, most recent first."""
    return llm_history.get_all()


@app.delete("/llm-history")
def clear_llm_history():
    llm_history.clear()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
    )
