"""
Pydantic schemas for inter-agent payloads and final output.
All fields are dicts (not Pydantic objects) in GraphState for LangGraph compatibility.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ResolvedContext(BaseModel):
    occasion: str
    formality_target: int           # 1-5, inferred from occasion + dress_code
    season: str                     # spring / summer / autumn / winter
    weather_summary: str            # "14°C, partly cloudy, light wind"
    city: Optional[str] = None
    dress_code: Optional[str] = None
    who_with: Optional[str] = None
    style_preferences: list[str] = []
    avoid_items: list[str] = []     # item_ids worn recently for same occasion


class OutfitItem(BaseModel):
    item_id: str
    name: str
    category: str
    subcategory: str
    color: str
    formality: int
    reason: str                     # per-item reasoning from outfit agent


class OutfitResult(BaseModel):
    items: list[OutfitItem]         # ordered: top → bottom → shoes → accessories
    confidence: float               # 0.0 – 1.0
    retry_count: int = 0
    search_query_used: str = ""


class OccasionResult(BaseModel):
    approved: bool
    confidence: float
    formality_ok: bool
    weather_ok: bool
    repeat_wear_flag: bool
    suggestions: list[str] = []     # adjustment suggestions if not approved
    notes: str = ""


class GapResult(BaseModel):
    complete: bool
    missing_categories: list[str] = []
    gap_queries: list[str] = []     # pre-formatted shopping search strings
    message: str = ""               # human-readable gap summary


class FinalOutfit(BaseModel):
    outfit_id: str
    occasion: str
    items: list[OutfitItem]
    weather_summary: str
    occasion_notes: str
    gap_message: str
    color_palette: str              # dominant palette from graph
    ready_to_wear: bool             # True if occasion_result approved + gap complete
