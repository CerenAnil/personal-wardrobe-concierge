"""
RAGAS Evaluation Harness — Personal Wardrobe Concierge

Evaluates retrieval and generation quality against the 50 held-out eval queries.

Metrics:
  Custom (no LLM, always run):
    recall@5    - fraction of ground-truth items found in top-5 results
    recall@10   - fraction of ground-truth items found in top-10 results
    precision@5 - fraction of top-5 results that are in ground truth

  RAGAS (LLM judge, requires ANTHROPIC_API_KEY):
    context_precision  - are retrieved item contexts relevant to the query?
    context_recall     - do retrieved contexts cover the ground truth?
    faithfulness       - is the outfit reasoning grounded in retrieved contexts?
    answer_relevancy   - does the outfit recommendation match the occasion?

Usage:
  python src/eval/ragas_eval.py                    # all 50 queries, all metrics
  python src/eval/ragas_eval.py --limit 10         # first 10 queries only
  python src/eval/ragas_eval.py --retrieval-only   # skip LLM metrics
  python src/eval/ragas_eval.py --output results.json

Output:
  data/eval/ragas_results.json   (unless --output overrides)
  console summary table
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.retrieval.hybrid_search import search
from src.db.sqlite_client import get_item

QUERIES_PATH = os.path.join("data", "eval", "ragas_queries.json")
DEFAULT_OUT  = os.path.join("data", "eval", "ragas_results.json")


# ---------------------------------------------------------------------------
# Document builder (same format as ChromaDB corpus)
# ---------------------------------------------------------------------------
def _item_to_doc(item: dict) -> str:
    parts = [
        item.get("name", ""),
        item.get("subcategory", ""),
        item.get("color", ""),
        item.get("material", ""),
        " ".join(item.get("occasions", [])) if isinstance(item.get("occasions"), list) else item.get("occasions", ""),
        " ".join(item.get("style_tags", [])) if isinstance(item.get("style_tags"), list) else item.get("style_tags", ""),
        item.get("notes", ""),
    ]
    return " | ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Custom retrieval metrics (no LLM)
# ---------------------------------------------------------------------------
@dataclass
class RetrievalMetrics:
    query: str
    occasion: str
    formality: int
    ground_truth_ids: list[str]
    retrieved_ids_5: list[str]
    retrieved_ids_10: list[str]
    recall_at_5: float
    recall_at_10: float
    precision_at_5: float
    avg_precision: float    # AP over ranks 1-10


def _average_precision(retrieved: list[str], relevant: set[str]) -> float:
    """Mean Average Precision over the retrieved list."""
    hits = 0
    score = 0.0
    for rank, item_id in enumerate(retrieved, start=1):
        if item_id in relevant:
            hits += 1
            score += hits / rank
    return score / max(len(relevant), 1)


def compute_retrieval_metrics(query_row: dict) -> RetrievalMetrics:
    query    = query_row["query"]
    occasion = query_row["occasion"]
    formality = query_row["formality"]
    gt_ids   = set(query_row["ground_truth_ids"])

    result_10 = search(query, n=10, formality_min=max(1, formality - 1), formality_max=min(5, formality + 1))
    retrieved_10 = [item.item_id for item in result_10.items]
    retrieved_5  = retrieved_10[:5]

    def recall(retrieved, gt):
        if not gt:
            return 1.0
        return len(set(retrieved) & gt) / len(gt)

    def precision(retrieved, gt):
        if not retrieved:
            return 0.0
        return len(set(retrieved) & gt) / len(retrieved)

    return RetrievalMetrics(
        query=query,
        occasion=occasion,
        formality=formality,
        ground_truth_ids=list(gt_ids),
        retrieved_ids_5=retrieved_5,
        retrieved_ids_10=retrieved_10,
        recall_at_5=round(recall(retrieved_5, gt_ids), 3),
        recall_at_10=round(recall(retrieved_10, gt_ids), 3),
        precision_at_5=round(precision(retrieved_5, gt_ids), 3),
        avg_precision=round(_average_precision(retrieved_10, gt_ids), 3),
    )


# ---------------------------------------------------------------------------
# Outfit recommendation text (for RAGAS response field)
# ---------------------------------------------------------------------------
def _build_outfit_response(query: str, retrieved_ids: list[str], occasion: str) -> str:
    """
    Call the outfit agent to produce a natural-language recommendation.
    Falls back to a listing of top retrieved items if the LLM is unavailable.
    """
    try:
        import anthropic
        from src.agents.outfit_agent import _build_user_prompt, _parse_llm_response, WORKER_MODEL

        resolved = {
            "occasion": occasion,
            "formality_target": 3,
            "season": "spring",
            "weather_summary": "comfortable weather",
            "style_preferences": ["classic", "minimal"],
            "avoid_items": [],
        }

        items = [get_item(iid) for iid in retrieved_ids if get_item(iid)]
        candidates = [
            {
                "item_id":     i["id"],
                "name":        i["name"],
                "category":    i["category"],
                "subcategory": i.get("subcategory", ""),
                "color":       i.get("color", ""),
                "color_family": i.get("color_family", "neutral"),
                "formality":   i["formality"],
                "occasions":   i.get("occasions", []),
                "style_tags":  i.get("style_tags", []),
            }
            for i in items[:12] if i
        ]

        prompt = _build_user_prompt(resolved, candidates, "No graph context.")
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=WORKER_MODEL, max_tokens=800,
            system="You are a personal stylist. Respond ONLY with valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        outfit_items, _ = _parse_llm_response(resp.content[0].text, candidates)
        if outfit_items:
            lines = [f"Outfit for {occasion}:"]
            for oi in outfit_items:
                lines.append(f"- {oi.name} ({oi.category}): {oi.reason}")
            return "\n".join(lines)
    except Exception:
        pass

    # Fallback: plain listing
    lines = [f"Suggested outfit for {occasion}:"]
    for iid in retrieved_ids[:6]:
        item = get_item(iid)
        if item:
            lines.append(f"- {item['name']} ({item['category']}, formality {item['formality']})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RAGAS evaluation
# ---------------------------------------------------------------------------
def run_ragas_eval(
    queries: list[dict],
    retrieval_results: list[RetrievalMetrics],
) -> dict:
    """
    Build RAGAS EvaluationDataset and run Faithfulness + AnswerRelevancy +
    ContextPrecision + ContextRecall with Claude haiku as the LLM judge.
    """
    from ragas import evaluate, EvaluationDataset
    from ragas.dataset_schema import SingleTurnSample
    from ragas.metrics.collections import (
        Faithfulness,
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
    )
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_anthropic import ChatAnthropic
    from langchain_community.embeddings import HuggingFaceEmbeddings

    print("  Configuring RAGAS with Claude haiku judge...")
    llm = LangchainLLMWrapper(
        ChatAnthropic(model=os.getenv("WORKER_MODEL", "claude-haiku-4-5-20251001"))
    )
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    )

    samples = []
    print("  Building RAGAS samples (generating outfit responses)...")
    for i, (q, rm) in enumerate(zip(queries, retrieval_results)):
        print(f"    [{i+1:02d}/{len(queries)}] {q['occasion']:15s} | {q['query'][:50]}")

        # Retrieved contexts as text
        contexts = []
        for iid in rm.retrieved_ids_10:
            item = get_item(iid)
            if item:
                contexts.append(_item_to_doc(item))

        # Reference: ground-truth items as text
        gt_texts = []
        for iid in q["ground_truth_ids"]:
            item = get_item(iid)
            if item:
                gt_texts.append(_item_to_doc(item))
        reference = f"Expected for {q['occasion']} (formality {q['formality']}): " + \
                    "; ".join(gt_texts)

        # Response: outfit recommendation from LLM
        response = _build_outfit_response(q["query"], rm.retrieved_ids_10, q["occasion"])
        time.sleep(0.5)  # avoid rate-limiting haiku

        samples.append(SingleTurnSample(
            user_input=q["query"],
            retrieved_contexts=contexts,
            response=response,
            reference=reference,
        ))

    dataset = EvaluationDataset(samples=samples)

    metrics = [
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
    ]

    print("  Running RAGAS evaluate()...")
    results = evaluate(dataset=dataset, metrics=metrics)
    return results.to_pandas().to_dict(orient="list")


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------
def _print_retrieval_summary(results: list[RetrievalMetrics]) -> None:
    print("\n" + "=" * 68)
    print(f"{'RETRIEVAL METRICS':^68}")
    print("=" * 68)
    print(f"{'Occasion':18s}  {'R@5':>6} {'R@10':>6} {'P@5':>6} {'MAP':>6}")
    print("-" * 68)

    # Group by occasion
    from collections import defaultdict
    by_occ: dict[str, list] = defaultdict(list)
    for r in results:
        by_occ[r.occasion].append(r)

    all_r5, all_r10, all_p5, all_map = [], [], [], []
    for occ in sorted(by_occ):
        rows = by_occ[occ]
        r5  = sum(r.recall_at_5    for r in rows) / len(rows)
        r10 = sum(r.recall_at_10   for r in rows) / len(rows)
        p5  = sum(r.precision_at_5 for r in rows) / len(rows)
        ap  = sum(r.avg_precision   for r in rows) / len(rows)
        print(f"{occ:18s}  {r5:6.3f} {r10:6.3f} {p5:6.3f} {ap:6.3f}  (n={len(rows)})")
        all_r5.append(r5); all_r10.append(r10); all_p5.append(p5); all_map.append(ap)

    print("-" * 68)
    n = len(by_occ)
    print(f"{'MEAN':18s}  {sum(all_r5)/n:6.3f} {sum(all_r10)/n:6.3f} {sum(all_p5)/n:6.3f} {sum(all_map)/n:6.3f}")
    print("=" * 68)


def _print_ragas_summary(ragas_dict: dict) -> None:
    print("\n" + "=" * 50)
    print(f"{'RAGAS METRICS (mean)':^50}")
    print("=" * 50)
    metric_keys = [k for k in ragas_dict if k not in ("user_input", "response", "retrieved_contexts", "reference")]
    for key in metric_keys:
        vals = [v for v in ragas_dict[key] if v is not None]
        mean = sum(vals) / len(vals) if vals else 0.0
        print(f"  {key:30s}  {mean:.4f}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="RAGAS evaluation for Wardrobe Concierge")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only first N queries")
    parser.add_argument("--retrieval-only", action="store_true", help="Skip LLM-based RAGAS metrics")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Output JSON path")
    args = parser.parse_args()

    if not os.path.exists(QUERIES_PATH):
        print(f"ERROR: {QUERIES_PATH} not found. Run: python scripts/generate_seed_data.py")
        sys.exit(1)

    with open(QUERIES_PATH) as f:
        all_queries = json.load(f)

    queries = all_queries[:args.limit] if args.limit else all_queries
    print(f"Evaluating {len(queries)} queries...")

    # ── Retrieval metrics (always) ─────────────────────────────────────────
    print("\n[1/2] Computing retrieval metrics...")
    retrieval_results: list[RetrievalMetrics] = []
    for i, q in enumerate(queries):
        rm = compute_retrieval_metrics(q)
        retrieval_results.append(rm)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(queries)} done")

    _print_retrieval_summary(retrieval_results)

    # ── RAGAS LLM metrics (optional) ──────────────────────────────────────
    ragas_results = None
    if not args.retrieval_only:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n[2/2] RAGAS metrics skipped (ANTHROPIC_API_KEY not set)")
            print("      Run with --retrieval-only to suppress this message, or set the key.")
        else:
            print("\n[2/2] Running RAGAS LLM evaluation...")
            try:
                ragas_results = run_ragas_eval(queries, retrieval_results)
                _print_ragas_summary(ragas_results)
            except Exception as e:
                print(f"  RAGAS evaluation failed: {e}")

    # ── Save results ───────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    output = {
        "run_at":   datetime.now().isoformat(),
        "n_queries": len(queries),
        "retrieval": [asdict(r) for r in retrieval_results],
        "ragas":     ragas_results,
    }
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
