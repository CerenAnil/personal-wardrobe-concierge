"""
Week 12 — Small Model Strategy Benchmark

Compares claude-haiku vs qwen/qwen3.5-9b (LM Studio) on the outfit selection task.

Runs N eval queries through both models and reports:
  - Latency (ms)
  - Estimated cost (USD)
  - Quality score: valid JSON, correct fields, items cover required categories

Usage:
  python scripts/benchmark_models.py
  python scripts/benchmark_models.py --n 10
  python scripts/benchmark_models.py --models claude-haiku-4-5-20251001 qwen/qwen3.5-9b
  python scripts/benchmark_models.py --output results/benchmark.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from src.llm.client import chat_full

# ---------------------------------------------------------------------------
# Pricing table (USD per million tokens, as of April 2026)
# Local models billed at $0 — just electricity
# ---------------------------------------------------------------------------
PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-haiku-4-5":          {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-6":         {"input": 3.00, "output": 15.00},
    # Local models — free
}

DEFAULT_MODELS = [
    "claude-haiku-4-5-20251001",
    "qwen/qwen3.5-9b",
]

OUTFIT_SYSTEM = """You are a personal stylist building a complete outfit from a wardrobe.
Select one item per category where possible (top, bottom, shoes, accessories).
If a dress is selected (subcategory="dress"), do NOT also select a separate bottom.
Consider color coordination, formality alignment, and the occasion.
Respond ONLY with valid JSON — no markdown, no extra text."""

# ---------------------------------------------------------------------------
# Load eval queries + wardrobe
# ---------------------------------------------------------------------------
def load_eval_queries(n: int) -> list[dict]:
    path = os.path.join("data", "eval", "ragas_queries.json")
    with open(path) as f:
        queries = json.load(f)
    return queries[:n]


def load_wardrobe_sample() -> list[dict]:
    """Return a representative 20-item sample for prompts (keeps prompts short)."""
    path = os.path.join("data", "seed", "wardrobe_items.json")
    with open(path) as f:
        items = json.load(f)
    # Take every 3rd item to get a spread across categories
    return items[::3][:20]


# ---------------------------------------------------------------------------
# Build outfit prompt (same format as outfit_agent.py)
# ---------------------------------------------------------------------------
def build_prompt(query: dict, candidates: list[dict]) -> str:
    occasion  = query.get("occasion", "casual")
    formality = query.get("formality", 3)

    lines = []
    for c in candidates:
        tags = c.get("style_tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        lines.append(
            f'  {c["item_id"]} | {c["name"]:35s} | {c["category"]:12s} | '
            f'formality={c["formality"]} | color={c["color"]} | tags={tags}'
        )

    return f"""Build a complete outfit for this occasion.

OCCASION: {occasion}
FORMALITY TARGET: {formality}/5
SEASON: spring
WEATHER: 14°C, partly cloudy
STYLE PREFERENCES: classic, minimal
USER STYLE PROFILE:
GENDER: women
STYLE NOTES: classic, minimal, neutral palette

CANDIDATE ITEMS:
{chr(10).join(lines)}

Select items to form a complete outfit (top, bottom, shoes, + optional accessories).
If a dress is chosen, do not also pick a separate bottom.
Prioritize formality {formality} items. Match colors.

Respond in this exact JSON format:
{{
  "items": [
    {{"item_id": "item_XXX", "name": "...", "category": "...", "subcategory": "...", "color": "...", "formality": N, "reason": "one sentence"}},
    ...
  ],
  "confidence": 0.0
}}"""


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------
def score_response(raw: str, query: dict) -> dict:
    """
    Returns a quality dict with individual pass/fail checks and an overall score 0-100.
    """
    checks = {
        "valid_json":        False,
        "has_items":         False,
        "item_count_ok":     False,   # 3-5 items
        "covers_categories": False,   # at least tops/dress + shoes
        "formality_aligned": False,   # avg formality within +-1 of target
        "has_reasons":       False,   # each item has a reason
    }

    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    # Strip <think>...</think> tags that Qwen3 sometimes emits
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    try:
        data  = json.loads(cleaned)
        items = data.get("items", [])
        checks["valid_json"] = True
        checks["has_items"]  = len(items) > 0

        if items:
            checks["item_count_ok"] = 3 <= len(items) <= 6
            cats = {i.get("category", "").lower() for i in items}
            sub  = {i.get("subcategory", "").lower() for i in items}
            has_top = "tops" in cats or "dress" in sub
            has_shoes = "shoes" in cats
            checks["covers_categories"] = has_top and has_shoes

            target   = query.get("formality", 3)
            formalities = [i.get("formality", 0) for i in items if i.get("formality")]
            if formalities:
                avg_f = mean(formalities)
                checks["formality_aligned"] = abs(avg_f - target) <= 1.2

            checks["has_reasons"] = all(
                bool(i.get("reason", "").strip()) for i in items
            )
    except Exception:
        pass

    score = sum(checks.values()) / len(checks) * 100
    return {"checks": checks, "score": round(score, 1)}


# ---------------------------------------------------------------------------
# Run benchmark for one model
# ---------------------------------------------------------------------------
def _model_max_tokens(model: str) -> int:
    """
    Local models (Qwen3.5-9B on consumer hardware) generate ~12 tok/s.
    1500 tokens gives ~115 s per query -- enough for a 5-item verbose JSON
    without the run hanging for 5+ minutes.
    Claude haiku is much faster, so 1024 is sufficient there.
    """
    if model.startswith("claude-"):
        return 1024
    return 1500


def _system_for_model(model: str, base_system: str) -> str:
    """
    Qwen3 in thinking mode uses <think>...</think> blocks that can exhaust token budgets.
    Appending /no_think disables chain-of-thought for fast structured-output tasks.
    """
    if "qwen" in model.lower():
        return base_system + "\n/no_think"
    return base_system


def benchmark_model(model: str, queries: list[dict], candidates: list[dict]) -> list[dict]:
    results = []
    system = _system_for_model(model, OUTFIT_SYSTEM)
    max_tok = _model_max_tokens(model)
    print(f"\n  Model: {model}  (max_tokens={max_tok})")
    print(f"  {'Query':<45} {'Latency':>10} {'Score':>7} {'Tokens':>8}")
    print(f"  {'-'*45} {'-'*10} {'-'*7} {'-'*8}")

    for q in queries:
        prompt = build_prompt(q, candidates)
        try:
            resp   = chat_full(model, system, prompt, max_tokens=max_tok)
            quality = score_response(resp.text, q)
            tokens  = resp.input_tokens + resp.output_tokens

            # Cost estimate
            pricing = PRICE_TABLE.get(model, {"input": 0.0, "output": 0.0})
            cost_usd = (
                resp.input_tokens  / 1_000_000 * pricing["input"] +
                resp.output_tokens / 1_000_000 * pricing["output"]
            )

            row = {
                "query":        q.get("query", "")[:45],
                "occasion":     q.get("occasion", ""),
                "latency_ms":   round(resp.latency_ms),
                "input_tokens": resp.input_tokens,
                "output_tokens": resp.output_tokens,
                "cost_usd":     round(cost_usd, 6),
                "quality":      quality,
                "error":        None,
            }
            print(f"  {row['query']:<45} {row['latency_ms']:>9}ms {quality['score']:>6.0f}% {tokens:>8}")

        except Exception as e:
            row = {
                "query":        q.get("query", "")[:45],
                "occasion":     q.get("occasion", ""),
                "latency_ms":   0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd":     0,
                "quality":      {"checks": {}, "score": 0},
                "error":        str(e)[:120],
            }
            print(f"  {row['query']:<45} {'ERROR':>10} {'0':>7}%")

        results.append(row)

    return results


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
def print_summary(all_results: dict[str, list[dict]]) -> None:
    print("\n" + "=" * 72)
    print(f"{'BENCHMARK SUMMARY':^72}")
    print("=" * 72)
    print(f"{'Model':<35} {'Avg Latency':>12} {'Avg Quality':>12} {'Est. Cost/10q':>14}")
    print(f"{'-'*35} {'-'*12} {'-'*12} {'-'*14}")

    for model, rows in all_results.items():
        successful = [r for r in rows if r["error"] is None]
        if not successful:
            print(f"{model:<35} {'N/A':>12} {'N/A':>12} {'N/A':>14}")
            continue

        avg_lat   = mean(r["latency_ms"] for r in successful)
        avg_qual  = mean(r["quality"]["score"] for r in successful)
        total_cost = sum(r["cost_usd"] for r in successful)
        is_local  = not model.startswith("claude-")
        cost_str  = "free (local)" if is_local else f"${total_cost:.4f}"

        print(f"{model:<35} {avg_lat:>10.0f}ms {avg_qual:>11.0f}% {cost_str:>14}")

    print("=" * 72)

    # Per-check breakdown
    print("\nQuality check breakdown:")
    check_names = [
        "valid_json", "has_items", "item_count_ok",
        "covers_categories", "formality_aligned", "has_reasons",
    ]
    header = f"{'Check':<25}" + "".join(f"{m[:16]:>18}" for m in all_results)
    print(header)
    print("-" * len(header))
    for check in check_names:
        row_str = f"{check:<25}"
        for rows in all_results.values():
            successful = [r for r in rows if r["error"] is None and check in r["quality"]["checks"]]
            pct = mean(r["quality"]["checks"][check] for r in successful) * 100 if successful else 0
            row_str += f"{pct:>17.0f}%"
        print(row_str)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LLM models on outfit selection task")
    parser.add_argument("--n",      type=int, default=10,             help="Number of eval queries to run (default 10)")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="Model identifiers to benchmark")
    parser.add_argument("--output", type=str,  default=None,          help="Save full results to JSON file")
    args = parser.parse_args()

    print(f"Wardrobe Concierge — Model Benchmark")
    print(f"Queries: {args.n}  |  Models: {', '.join(args.models)}")
    print(f"LM Studio URL: {os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')}")

    queries    = load_eval_queries(args.n)
    candidates = load_wardrobe_sample()

    print(f"\nLoaded {len(queries)} queries, {len(candidates)} candidate items")

    all_results: dict[str, list[dict]] = {}
    for model in args.models:
        all_results[model] = benchmark_model(model, queries, candidates)

    print_summary(all_results)

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nFull results saved to {args.output}")


if __name__ == "__main__":
    main()
