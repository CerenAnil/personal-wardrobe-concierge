"""
Gap Finder MCP Server — stdio transport, FastMCP.

Analyzes a proposed outfit for missing pieces and returns natural-language
gap descriptions + pre-formatted shopping search queries.

Completeness rules:
  - All outfits need:  top + bottom + shoes
  - Formality 3+:      at least one accessory
  - Formality 4-5:     outerwear or blazer required

Tools:
  find_gaps(proposed_outfit, occasion, formality)

Start: python src/mcp/gap_finder_server.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gap-finder-server")

# Category groups
OUTERWEAR_SUBCATEGORIES = {"blazer", "coat", "trench coat", "jacket", "overcoat"}


def _has_category(outfit: list[dict], category: str) -> bool:
    return any(
        item.get("category", "").lower() == category.lower()
        for item in outfit
    )


def _has_outerwear_or_blazer(outfit: list[dict]) -> bool:
    for item in outfit:
        if item.get("category", "").lower() == "outerwear":
            return True
    return False


def _has_accessory(outfit: list[dict]) -> bool:
    return _has_category(outfit, "accessories")


def _build_gap_query(
    missing_cat: str,
    occasion: str,
    formality: int,
    outfit_colors: list[str],
    outfit_styles: list[str],
) -> str:
    """
    Build a pre-formatted search query for a missing category.
    Incorporates dominant color and style context for shopping relevance.
    """
    # Style hint from outfit context
    style = outfit_styles[0] if outfit_styles else "classic"

    # Color hint — prefer neutral bridge or most common color
    color_map = {"neutral": "black", "cool": "navy", "warm": "camel", "earth": "brown"}
    color_families = [c for c in outfit_colors if c in color_map]
    color_hint = color_map.get(color_families[0], "black") if color_families else "black"

    formality_words = {
        1: "casual",
        2: "smart-casual",
        3: "smart",
        4: "formal",
        5: "black tie",
    }
    formality_label = formality_words.get(formality, "smart")

    templates: dict[str, str] = {
        "tops":        f"{formality_label} {style} top {occasion}",
        "bottoms":     f"{formality_label} {color_hint} {style} trousers {occasion}",
        "shoes":       f"{formality_label} {color_hint} {style} shoes {occasion}",
        "accessories": f"{formality_label} {style} accessories {occasion}",
        "outerwear":   f"{formality_label} {color_hint} {style} blazer coat {occasion}",
    }
    return templates.get(missing_cat, f"{formality_label} {missing_cat} {occasion}")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
@mcp.tool()
def find_gaps(
    proposed_outfit: list[dict],
    occasion: str,
    formality: int,
) -> dict:
    """
    Analyze a proposed outfit for missing pieces based on occasion and formality rules.

    Args:
        proposed_outfit: List of item dicts (must include 'category', 'subcategory',
                         'color_family', 'style_tags' fields)
        occasion:        Occasion name (e.g. "dinner", "job-interview", "gym")
        formality:       Target formality level 1-5

    Returns:
        {
          complete: bool,
          missing_categories: list[str],
          gap_queries: list[str],    # pre-formatted shopping search strings
          message: str               # human-readable gap summary
        }
    """
    missing: list[str] = []

    has_top        = _has_category(proposed_outfit, "tops")
    has_bottom     = _has_category(proposed_outfit, "bottoms")
    has_shoes      = _has_category(proposed_outfit, "shoes")
    has_outerwear  = _has_outerwear_or_blazer(proposed_outfit)
    has_accessory  = _has_accessory(proposed_outfit)

    # Core requirements — every outfit
    if not has_top:
        missing.append("tops")
    if not has_bottom:
        missing.append("bottoms")
    if not has_shoes:
        missing.append("shoes")

    # Formality-driven requirements
    if formality >= 4 and not has_outerwear:
        missing.append("outerwear")
    if formality >= 3 and not has_accessory:
        missing.append("accessories")

    # Build context for gap query generation
    outfit_colors = [
        item.get("color_family", "neutral")
        for item in proposed_outfit
    ]
    outfit_styles: list[str] = []
    for item in proposed_outfit:
        tags = item.get("style_tags", [])
        if isinstance(tags, str):
            tags = tags.split(",")
        outfit_styles.extend(tags)

    gap_queries = [
        _build_gap_query(cat, occasion, formality, outfit_colors, outfit_styles)
        for cat in missing
    ]

    # Human-readable message
    if not missing:
        message = "Outfit is complete."
    elif len(missing) == 1:
        message = (
            f"The outfit is missing {missing[0]}. "
            f"For {occasion} at formality {formality}, try: \"{gap_queries[0]}\""
        )
    else:
        items_str = ", ".join(missing[:-1]) + f" and {missing[-1]}"
        queries_str = " | ".join(f'"{q}"' for q in gap_queries)
        message = (
            f"The outfit is missing {items_str}. "
            f"Suggested searches: {queries_str}"
        )

    return {
        "complete":           len(missing) == 0,
        "missing_categories": missing,
        "gap_queries":        gap_queries,
        "message":            message,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
