"""
Wardrobe MCP Server — stdio transport, FastMCP.

Tools:
  search_items(query, filters)         full-text + filter search over wardrobe
  get_item(item_id)                    fetch a single item by ID
  get_wear_history(item_id, limit)     recent wear log entries for an item
  log_outfit(outfit_id, item_ids, ...) write approved outfit to wear_log (WEAR_SECRET required)

Start: python src/mcp/wardrobe_server.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from mcp.server.fastmcp import FastMCP
from src.db.sqlite_client import (
    get_item as db_get_item,
    search_items as db_search_items,
    get_wear_history as db_get_wear_history,
    log_wear,
    save_outfit,
    approve_outfit,
)

mcp = FastMCP("wardrobe-server")

WEAR_SECRET = os.getenv("WEAR_SECRET", "")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def search_items(
    query: str = "",
    category: str = "",
    formality_min: int = 0,
    formality_max: int = 5,
    season: str = "",
    occasion: str = "",
    limit: int = 20,
) -> list[dict]:
    """
    Full-text + filter search over the wardrobe SQLite database.

    Args:
        query:        Free-text search across name, subcategory, color, style_tags, notes
        category:     Filter by category (tops/bottoms/outerwear/shoes/accessories)
        formality_min: Minimum formality level (1-5)
        formality_max: Maximum formality level (1-5)
        season:       Filter by season (spring/summer/autumn/winter)
        occasion:     Filter by occasion (work/dinner/casual/gym/job-interview/wedding-guest...)
        limit:        Max results (default 20)

    Returns:
        List of matching wardrobe item dicts.
    """
    return db_search_items(
        query=query,
        category=category or None,
        formality_min=formality_min if formality_min > 0 else None,
        formality_max=formality_max if formality_max < 5 else None,
        season=season or None,
        occasion=occasion or None,
        limit=limit,
    )


@mcp.tool()
def get_item(item_id: str) -> dict:
    """
    Fetch a single wardrobe item by ID.

    Args:
        item_id: Item identifier (e.g. "item_001")

    Returns:
        Item dict, or {"error": "not found"} if the ID doesn't exist.
    """
    item = db_get_item(item_id)
    if item is None:
        return {"error": f"item {item_id!r} not found"}
    return item


@mcp.tool()
def get_wear_history(item_id: str, limit: int = 10) -> list[dict]:
    """
    Return the most recent wear log entries for an item.

    Args:
        item_id: Item identifier
        limit:   Max entries to return (default 10)

    Returns:
        List of wear_log dicts ordered by worn_on DESC.
    """
    return db_get_wear_history(item_id, limit=limit)


@mcp.tool()
def log_outfit(
    outfit_id: str,
    item_ids: list[str],
    occasion: str,
    worn_on: str,
    weather_summary: str = "",
    context_json: str = "{}",
    secret: str = "",
) -> dict:
    """
    Write an approved outfit to the wear_log and outfits tables.

    This tool is WEAR_SECRET-gated — the secret must match the server's
    WEAR_SECRET env var. Agents must NOT receive the secret directly;
    only the LangGraph record_wear node passes it.

    Args:
        outfit_id:       Unique outfit ID (e.g. "outfit_20260411_abc")
        item_ids:        List of item IDs worn in this outfit
        occasion:        Occasion name
        worn_on:         ISO date string (YYYY-MM-DD)
        weather_summary: e.g. "14°C, partly cloudy"
        context_json:    JSON string of the full ResolvedContext
        secret:          Must match WEAR_SECRET env var

    Returns:
        {"status": "logged", "outfit_id": ...} or {"error": ...}
    """
    if not WEAR_SECRET or secret != WEAR_SECRET:
        return {"error": "invalid or missing WEAR_SECRET"}

    try:
        save_outfit({
            "id": outfit_id,
            "occasion": occasion,
            "context_json": context_json,
            "item_ids": item_ids,
            "worn_on": worn_on,
            "approved": 1,
        })
        for item_id in item_ids:
            log_wear(
                item_id=item_id,
                outfit_id=outfit_id,
                occasion=occasion,
                worn_on=worn_on,
                weather_summary=weather_summary,
            )
        approve_outfit(outfit_id)
        return {"status": "logged", "outfit_id": outfit_id, "items_logged": len(item_ids)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
