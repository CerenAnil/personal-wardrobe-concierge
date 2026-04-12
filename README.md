# Wardrobe Concierge

A multi-agent AI stylist that knows your wardrobe. Describe an occasion and it builds a complete outfit, flags missing pieces, and remembers what you've worn.

![Empty state](docs/screenshots/empty-state.png)

![Outfit card](docs/screenshots/outfit-card.png)

---

## What it does

- **Hybrid retrieval** - BM25 keyword search + ChromaDB vector search fused with RRF (k=60) over a 60-item wardrobe
- **Graph-aware selection** - Neo4j PAIRS_WITH / CLASHES_WITH edges steer the outfit agent away from clashing combinations
- **Real weather** - Open-Meteo geocoding + forecast API; outfit formality and layering adapt to conditions
- **Gap detection** - flags missing categories (top, bottom, shoes, accessory) and generates shopping search queries
- **Human-in-the-loop** - LangGraph HITL interrupt blocks wear logging until you approve; wear history is never written silently
- **Per-user memory** - avoids repeating outfits worn within the last 30 days for the same occasion

---

## Architecture

```
User query
    |
    v
Manager Agent (resolve)       <- weather + user memory + formality inference
    |
    v
Outfit Agent                  <- hybrid BM25+vector search + graph context + LLM selection
    |         \
    v          v
Occasion      Gap Agent       <- parallel fan-out
Reasoner
    |         /
    v        v
Manager Agent (aggregate)     <- palette coherence check + FinalOutfit
    |
    v
HITL Gate  <-- interrupt()    <- user approves or declines via /approve
    |
    v
Record Wear                   <- SQLite wear_log + Neo4j WORN_TOGETHER + user memory update
```

**Models:** `claude-sonnet-4-6` (Manager), `claude-haiku-4-5-20251001` (Workers)

**Stack:** LangGraph - FastMCP - ChromaDB - Neo4j AuraDB - rank-bm25 - FastAPI - sentence-transformers

---

## Project structure

```
personal-wardrobe-concierge/
├── data/
│   ├── seed/
│   │   ├── wardrobe_items.json    60 synthetic items (seed=42)
│   │   └── wardrobe.db            SQLite database
│   ├── eval/
│   │   └── ragas_queries.json     50 RAGAS evaluation queries
│   └── memory/
│       └── user_001.json          Per-user wear history (runtime)
├── scripts/
│   ├── generate_seed_data.py      Generates wardrobe items + eval queries
│   ├── seed_all.py                Seeds SQLite + ChromaDB
│   └── seed_neo4j.py              Seeds Neo4j graph
├── src/
│   ├── models/                    GraphState TypedDict + Pydantic schemas
│   ├── db/                        SQLite, ChromaDB, Neo4j clients
│   ├── retrieval/                 Hybrid BM25+vector search, graph retrieval
│   ├── mcp/                       FastMCP servers: wardrobe, weather, gap finder
│   ├── memory/                    Per-user JSON memory
│   ├── agents/                    Manager, Outfit, Occasion, Gap agents
│   ├── graph/                     LangGraph nodes + workflow
│   ├── eval/                      RAGAS evaluation harness
│   └── api/                       FastAPI server
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── docs/
    └── screenshots/
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- Node.js (for the frontend dev server)
- Neo4j AuraDB Free account (or local Neo4j)
- Anthropic API key

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
NEO4J_URI=neo4j+s://...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
GEOCODING_API_KEY=...        # api-ninjas.com free key (for weather city lookup)
WEAR_SECRET=some-secret      # any string; gates wear logging
```

### 4. Generate and seed data

```bash
# Generate 60 wardrobe items + 50 eval queries
python scripts/generate_seed_data.py

# Seed SQLite + ChromaDB
python scripts/seed_all.py

# Seed Neo4j graph (PAIRS_WITH / CLASHES_WITH edges)
python scripts/seed_neo4j.py
```

### 5. Start the API server

```bash
python src/api/main.py
```

Server starts at `http://localhost:8000`.

### 6. Open the frontend

The API serves the frontend at `http://localhost:8000/`. Open it in a browser.

Or run the standalone frontend dev server (no backend needed for UI-only work):

```bash
npx serve -p 3131 frontend
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/outfit` | Build outfit for an occasion |
| `POST` | `/approve` | Approve or decline an outfit (HITL gate) |
| `GET` | `/memory/{user_id}` | Read user wear memory |
| `DELETE` | `/memory/{user_id}` | Clear user wear memory |
| `GET` | `/health` | Health check |

### POST /outfit

```json
{
  "raw_query": "smart casual dinner tonight",
  "user_id": "user_001",
  "city": "London",
  "dress_code": "smart casual",
  "who_with": "partner"
}
```

Response:

```json
{
  "status": "awaiting_approval",
  "session_id": "abc123",
  "outfit": {
    "occasion": "dinner",
    "items": [...],
    "color_palette": "navy & camel",
    "ready_to_wear": true,
    "weather_summary": "12°C, partly cloudy",
    "gap_message": "Outfit is complete."
  }
}
```

### POST /approve

```json
{ "session_id": "abc123", "approved": true }
```

---

## Evaluation

```bash
# Custom retrieval metrics only (no LLM, fast)
python src/eval/ragas_eval.py --retrieval-only --limit 20

# Full RAGAS evaluation (requires ANTHROPIC_API_KEY)
python src/eval/ragas_eval.py

# Save to custom path
python src/eval/ragas_eval.py --output results/run1.json
```

Metrics reported:

| Metric | Description |
|--------|-------------|
| Recall@5 | Fraction of ground-truth items in top-5 results |
| Recall@10 | Fraction of ground-truth items in top-10 results |
| Precision@5 | Fraction of top-5 results that are ground truth |
| MAP | Mean average precision over ranks 1-10 |
| Context Precision | Are retrieved contexts relevant to the query? |
| Context Recall | Do retrieved contexts cover the ground truth? |
| Faithfulness | Is the outfit reasoning grounded in retrieved contexts? |
| Answer Relevancy | Does the recommendation match the occasion? |

---

## How HITL works

The LangGraph workflow pauses at `hitl_gate` using `interrupt()`. The API returns `status: awaiting_approval` and holds the graph state in memory (keyed by `session_id`). When `POST /approve` is called, the graph resumes via `Command(resume={"approved": bool})`. If approved, the wear log is written; if declined, the graph exits cleanly without writing anything.

---

## Notes

- ChromaDB runs in embedded mode - no separate server needed. Persisted at `.cache/chroma/`.
- MCP servers use stdio transport - they are started as subprocesses by the API on startup.
- Neo4j PAIRS_WITH / CLASHES_WITH edges are computed once at seed time, not per query.
- The `WEAR_SECRET` env var is injected only at the `record_wear` node; agents never see it.
- `log_outfit` in the wardrobe MCP server verifies the secret before writing.
