# Architecture: Personal Wardrobe Concierge

## Project Identity

A personal AI stylist that knows your wardrobe. You describe the occasion, context, and constraints — it searches your clothes, builds a complete outfit, flags missing pieces, and remembers what you wore and when. Built as a local-first system for single-user use.

---

## Course Checkpoint Coverage

| Week | Topic | Implementation |
|------|-------|---------------|
| 5 | RAG 2.0 - Hybrid search + self-correcting loop | BM25 + vector search over wardrobe; low-confidence retry with relaxed filters |
| 6 | GraphRAG - Neo4j Knowledge Graph | Outfit compatibility graph: items, occasions, wear history as nodes + relationships |
| 7 | RAGAS Evaluation | 50 held-out occasion queries scored on context precision, faithfulness, answer relevancy |
| 8 | MCP Foundations | Wardrobe SQLite MCP server + live Weather API MCP server |
| 9 | Building MCP Servers | Custom gap-finder MCP tool: detects missing outfit pieces, returns a search query |
| 10 | Multi-Agent Workflows | Manager → Outfit Agent + Gap Agent + Occasion Reasoner (hierarchical fan-out) |
| 11 | HITL & Memory | Approval gate ("Did you wear this?") + per-outfit wear history in long-term memory |

---

## User Flow

```
User opens app
  → Selects occasion (dinner, job interview, gym, wedding guest...)
  → Enters optional context (weather city, dress code, who they're with)
  → System fetches live weather for their location
  → Agents search wardrobe, build outfit, check for gaps
  → Presents complete outfit card with reasoning
  → User approves / tweaks / declines
  → Memory records what was worn, when, and for what occasion
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│                                                                 │
│   POST /outfit    POST /approve    GET/DELETE /memory           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    LangGraph Workflow                           │
│                                                                 │
│   [resolve_context] ──► [outfit_search] ──┬──► [occasion_reason]│
│                                           └──► [gap_check]      │
│                                                     │           │
│                              [manager_aggregate] ◄──┘           │
│                                     │                           │
│                              [hitl_gate] ── interrupt()         │
│                                     │                           │
│                              [record_wear]                      │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
┌────────▼───────┐  ┌─────────▼──────┐  ┌─────────▼──────────┐
│  Hybrid Search │  │  Neo4j Graph   │  │   MCP Servers      │
│  BM25 + Chroma │  │  Outfit Graph  │  │  wardrobe + weather │
│  RRF k=60      │  │  + Wear Hist.  │  │  + gap finder      │
└────────────────┘  └────────────────┘  └────────────────────┘
         │                    │
┌────────▼───────┐  ┌─────────▼──────┐
│  SQLite        │  │  ChromaDB      │
│  Wardrobe DB   │  │  Embeddings    │
└────────────────┘  └────────────────┘
```

---

## Data Model

### Wardrobe Item (Excel import schema)

Users populate a spreadsheet with these columns. The import script reads it into SQLite and ChromaDB.

| Column | Type | Example |
|--------|------|---------|
| name | string | "Navy Slim Blazer" |
| category | string | tops / bottoms / outerwear / shoes / accessories |
| subcategory | string | blazer / jeans / sneakers / scarf |
| color | string | navy |
| color_family | string | cool / warm / neutral |
| material | string | wool-blend |
| formality | int (1-5) | 4 (1=gym, 5=black tie) |
| occasions | comma list | work, dinner, wedding-guest |
| seasons | comma list | autumn, winter |
| style_tags | comma list | classic, structured, minimal |
| owned_since | date | 2023-04-01 |
| last_worn | date | 2025-01-15 |
| notes | string | "runs slim, avoid tucking" |
| image_path | string | images/navy_blazer.jpg (optional) |

### SQLite Tables

```sql
-- Core wardrobe
CREATE TABLE items (
  id TEXT PRIMARY KEY,          -- item_001, item_002 ...
  name TEXT,
  category TEXT,
  subcategory TEXT,
  color TEXT,
  color_family TEXT,
  material TEXT,
  formality INTEGER,            -- 1-5
  occasions TEXT,               -- JSON list
  seasons TEXT,                 -- JSON list
  style_tags TEXT,              -- JSON list
  owned_since TEXT,
  last_worn TEXT,
  notes TEXT,
  image_path TEXT,
  active INTEGER DEFAULT 1      -- soft delete for retired items
);

-- Wear log (written on HITL approval)
CREATE TABLE wear_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT,
  outfit_id TEXT,               -- groups items worn together
  occasion TEXT,
  worn_on TEXT,                 -- ISO date
  weather_summary TEXT,         -- "14°C, partly cloudy"
  user_rating INTEGER,          -- 1-5 post-wear (future)
  notes TEXT
);

-- Outfit sessions (one row per approved outfit)
CREATE TABLE outfits (
  id TEXT PRIMARY KEY,          -- outfit_20250411_abc
  occasion TEXT,
  context_json TEXT,            -- full context at time of query
  item_ids TEXT,                -- JSON list
  worn_on TEXT,
  approved INTEGER
);
```

---

## Knowledge Graph (Neo4j)

### Node Types

| Node | Key Properties |
|------|---------------|
| Item | id, name, category, formality, color_family, style_tags |
| Occasion | name (dinner, interview, gym, wedding-guest...) |
| Season | name (spring, summer, autumn, winter) |
| ColorPalette | name (cool, warm, neutral, earth, monochrome) |
| Outfit | id, worn_on, rating |
| StyleCluster | name (minimal, maximalist, classic, streetwear...) |

### Relationship Types

| Relationship | From → To | Meaning |
|---|---|---|
| PAIRS_WITH | Item → Item | Styling compatibility (computed from co-wear + style rules) |
| CLASHES_WITH | Item → Item | Color or formality mismatch |
| SUITABLE_FOR | Item → Occasion | Formality-based suitability |
| WORN_IN | Item → Season | Season tags from import |
| BELONGS_TO_PALETTE | Item → ColorPalette | Color family grouping |
| WORN_TOGETHER | Item → Item | Actual co-wear history (from wear_log) |
| PART_OF | Item → Outfit | Outfit composition |
| HAS_STYLE | Item → StyleCluster | Style tag grouping |

### Graph Retrieval Patterns (3 Cypher queries)

```cypher
-- 1. Find items that pair well with a seed item (for outfit building)
MATCH (seed:Item {id: $seed_id})-[:PAIRS_WITH]->(candidate:Item)
WHERE NOT (seed)-[:CLASHES_WITH]-(candidate)
RETURN candidate ORDER BY candidate.formality DESC LIMIT 10

-- 2. Find outfits worn successfully for the same occasion
MATCH (o:Outfit)-[:SUITABLE_FOR]->(occ:Occasion {name: $occasion})
MATCH (i:Item)-[:PART_OF]->(o)
WHERE o.rating >= 4
RETURN o, collect(i) as items ORDER BY o.worn_on DESC LIMIT 5

-- 3. Detect color palette coherence of a proposed outfit
MATCH (i:Item)-[:BELONGS_TO_PALETTE]->(p:ColorPalette)
WHERE i.id IN $proposed_ids
RETURN p.name, count(i) as count ORDER BY count DESC
```

---

## MCP Servers

### 1. Wardrobe MCP Server (`src/mcp/wardrobe_server.py`)

Tools exposed to agents via FastMCP:

```python
@mcp.tool()
def search_items(query: str, filters: dict) -> list[dict]:
    """Full-text + filter search over wardrobe SQLite."""

@mcp.tool()
def get_item(item_id: str) -> dict:
    """Fetch a single item by ID."""

@mcp.tool()
def get_wear_history(item_id: str, limit: int = 10) -> list[dict]:
    """Recent wear log entries for an item."""

@mcp.tool()
def log_outfit(outfit_id: str, item_ids: list, occasion: str,
               worn_on: str, weather_summary: str) -> dict:
    """Write approved outfit to wear_log. Requires WEAR_SECRET."""
```

### 2. Weather MCP Server (`src/mcp/weather_server.py`)

Wraps the Open-Meteo API (free, no key required).

```python
@mcp.tool()
def get_weather(city: str, date: str) -> dict:
    """
    Returns: {
      temp_c: float,
      feels_like_c: float,
      condition: str,       # sunny / cloudy / rainy / snowy
      humidity_pct: int,
      wind_kph: float,
      summary: str          # "14°C, partly cloudy, light wind"
    }
    """
```

Used by `resolve_context` node to enrich the user query before agents run. Agents receive `weather_summary` in their context - they never call this tool directly.

### 3. Gap Finder MCP Server (`src/mcp/gap_finder_server.py`)

```python
@mcp.tool()
def find_gaps(proposed_outfit: list[dict], occasion: str,
              formality: int) -> dict:
    """
    Analyzes proposed outfit for missing pieces.
    Returns: {
      complete: bool,
      missing_categories: list[str],
      gap_queries: list[str]   # e.g. ["beige linen shirt minimal"]
    }
    """
```

Gap detection logic:
- Every outfit needs: top + bottom OR one-piece + shoes
- Formality 4-5 also requires: outerwear or blazer
- Formality 3+ also requires: at least one accessory
- Gap queries are pre-formatted for direct Google Shopping / ASOS search

---

## Agents

### Manager Agent (`src/agents/manager.py`)

**resolve()** - Reads occasion + optional context (city, dress code, who-with), calls `weather_server.get_weather()`, enriches state with:
```python
ResolvedContext(
  occasion: str,
  formality_target: int,      # inferred from occasion + dress_code
  season: str,                # inferred from weather date
  weather_summary: str,
  style_preferences: list,    # from user long-term memory
  avoid_items: list           # worn recently for same occasion
)
```

**aggregate()** - Combines outfit_agent + gap_agent + occasion_agent outputs into FinalOutfit. Checks color palette coherence via graph.

---

### Outfit Agent (`src/agents/outfit_agent.py`)

Worker model (claude-haiku). 3-attempt retry loop:
1. Hybrid search (BM25 + vector) with full context
2. Relax formality constraint ±1
3. Fall back to style_tags from memory only

Fetches graph context: PAIRS_WITH relationships for top candidate, WORN_TOGETHER history, past successful outfits for same occasion.

Outputs: `OutfitResult` - ordered list of items (top → bottom → shoes → accessories) with per-item reasoning.

---

### Occasion Reasoner Agent (`src/agents/occasion_agent.py`)

Worker model (claude-haiku). Validates the proposed outfit against the occasion:
- Checks formality alignment
- Flags weather mismatches (e.g. suede shoes + rain forecast)
- Flags repeat wear (same item worn for same occasion < 30 days ago)
- Returns confidence score + adjustment suggestions

---

### Gap Agent (`src/agents/gap_agent.py`)

Worker model (claude-haiku). Calls `gap_finder_server.find_gaps()`, formats the result into natural language:

```
"The outfit is missing shoes. For a dinner at formality 4,
try searching: 'chelsea boots black leather minimal'"
```

If outfit is complete, returns `complete=True` with no gap message.

---

## LangGraph Workflow

```
START
  └─► resolve_context          # enrich query with weather + memory
        └─► outfit_search      # hybrid search + graph retrieval
              ├─► occasion_reason   ─┐
              └─► gap_check         ─┴─► manager_aggregate
                                              └─► hitl_gate
                                                    │ interrupt()
                                          approved? │ declined?
                                              └─► record_wear
                                                    └─► END
```

**Fan-out:** `outfit_search` → `occasion_reason` and `gap_check` run in parallel (two `add_edge` calls, LangGraph handles join at `manager_aggregate`).

**HITL pattern:** `interrupt()` inside `hitl_gate` node. Resume via `Command(resume={"approved": bool})`. On approval, `record_wear` writes to `wear_log` and updates Neo4j `WORN_TOGETHER` edges.

---

## GraphState (TypedDict)

```python
class GraphState(TypedDict, total=False):
    # Input
    user_id: str
    raw_query: str
    session_id: str
    city: str
    dress_code: Optional[str]
    who_with: Optional[str]

    # Resolved context
    resolved_context: Optional[dict]    # ResolvedContext
    user_memory: Optional[dict]

    # Agent outputs
    outfit_result: Optional[dict]       # OutfitResult
    occasion_result: Optional[dict]     # OccasionResult
    gap_result: Optional[dict]          # GapResult

    # Final
    final_outfit: Optional[dict]        # FinalOutfit
    awaiting_human_approval: bool
    human_approved: bool

    # Control
    retry_count: int
    error: Optional[str]
```

---

## Memory (`src/memory/user_memory.py`)

Per-user JSON file at `data/memory/{user_id}.json`.

```json
{
  "user_id": "user_001",
  "style_preferences": ["minimal", "classic", "neutral-palette"],
  "avoid_styles": ["maximalist"],
  "recent_wear": [
    {
      "outfit_id": "outfit_20250410_abc",
      "occasion": "dinner",
      "item_ids": ["item_003", "item_011", "item_022"],
      "worn_on": "2025-04-10"
    }
  ],
  "occasion_history": {
    "job_interview": ["item_005", "item_009"],
    "dinner": ["item_003", "item_011"]
  },
  "total_sessions": 14
}
```

`avoid_items` in `ResolvedContext` is populated from `recent_wear` where `occasion == current_occasion` and `worn_on` within 30 days.

---

## Retrieval: Hybrid Search (`src/retrieval/hybrid_search.py`)

Corpus: all wardrobe items, one document per item.

Document format fed to BM25 + ChromaDB:
```
"{name} {subcategory} {color} {material} {occasions} {style_tags} {notes}"
```

Same RRF implementation as current project (k=60). Confidence < 0.6 triggers retry.

---

## Data Pipeline

### Excel Import (`scripts/import_wardrobe.py`)

```
wardrobe.xlsx
  └─► validate schema (required columns, formality 1-5, valid categories)
  └─► generate item IDs
  └─► write to SQLite items table
  └─► embed documents → ChromaDB
  └─► seed Neo4j nodes + SUITABLE_FOR + WORN_IN + BELONGS_TO_PALETTE edges
  └─► report: N items imported, M skipped (validation errors)
```

PAIRS_WITH edges are computed after import using style compatibility rules (same color family + adjacent formality ±1 + no category clash). CLASHES_WITH from conflicting color families (e.g. warm + cool without a neutral bridge).

### Seed Eval Queries (`scripts/generate_eval_queries.py`)

50 occasion queries with ground-truth item IDs for RAGAS. Format:
```json
{
  "query": "smart casual dinner, autumn evening, 18°C",
  "occasion": "dinner",
  "formality": 3,
  "expected_categories": ["tops", "bottoms", "shoes"],
  "ground_truth_ids": ["item_003", "item_011", "item_022"]
}
```

---

## Evaluation (`src/eval/ragas_eval.py`)

Same RAGAS harness as current project. Metrics:
- **context_precision** - did we retrieve the right items?
- **faithfulness** - is the outfit reasoning grounded in the retrieved items?
- **answer_relevancy** - does the suggestion match the occasion?

LLM-as-judge: `claude-haiku` scores each response against the ground truth.

---

## Frontend

Same vanilla HTML/CSS/JS stack. Key differences from store version:

| Element | Store Version | Wardrobe Version |
|---|---|---|
| Sidebar | User profile + location | Occasion selector + city + dress code + who-with |
| Empty state prompts | "Casual linen shirt..." | "Smart casual dinner tonight" / "Job interview tomorrow" |
| Basket card | Product name + aisle + price | Item name + why it works + last worn date |
| Route summary | Store navigation | Weather summary + outfit notes |
| Approval buttons | "Reserve items" / "Not today" | "Wearing this" / "Show me alternatives" |
| Post-approval | Stock reserved | Wear logged to memory |

---

## File Structure

```
wardrobe-concierge/
├── data/
│   ├── wardrobe.xlsx              # user's clothing spreadsheet (gitignored)
│   ├── seed/
│   │   └── wardrobe.db            # SQLite (gitignored)
│   ├── eval/
│   │   └── ragas_queries.json
│   └── memory/
│       └── user_001.json          # gitignored
├── scripts/
│   ├── import_wardrobe.py         # Excel → SQLite + ChromaDB + Neo4j
│   └── generate_eval_queries.py
├── src/
│   ├── models/
│   │   ├── graph_state.py
│   │   └── schemas.py             # ResolvedContext, OutfitResult, GapResult, FinalOutfit
│   ├── db/
│   │   ├── sqlite_client.py
│   │   └── neo4j_client.py
│   ├── retrieval/
│   │   ├── hybrid_search.py
│   │   └── graph_retrieval.py
│   ├── mcp/
│   │   ├── wardrobe_server.py
│   │   ├── weather_server.py
│   │   └── gap_finder_server.py
│   ├── memory/
│   │   └── user_memory.py
│   ├── agents/
│   │   ├── manager.py
│   │   ├── outfit_agent.py
│   │   ├── occasion_agent.py
│   │   └── gap_agent.py
│   ├── graph/
│   │   ├── nodes.py
│   │   └── workflow.py
│   ├── eval/
│   │   └── ragas_eval.py
│   └── api/
│       └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .env.example
├── architecture_wardrobe.md
└── agent.instructions.md
```

---

## Environment Variables

```env
# Anthropic
ANTHROPIC_API_KEY=

# Models
MANAGER_MODEL=claude-sonnet-4-6
WORKER_MODEL=claude-haiku-4-5-20251001

# Neo4j AuraDB
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=

# Paths
SQLITE_DB_PATH=data/seed/wardrobe.db
CHROMA_PERSIST_DIR=.cache/chroma
MEMORY_STORE_PATH=data/memory

# Security
WEAR_SECRET=

# API
API_HOST=0.0.0.0
API_PORT=8000

# Weather (Open-Meteo - no key needed, but geocoding needs city→lat/lon)
GEOCODING_API_KEY=         # free tier: api.api-ninjas.com or opencagedata.com
```

---

## Key Design Decisions

**Why Open-Meteo for weather?** Free, no rate limits for personal use, no key required for weather data. Only geocoding (city → lat/lon) needs a free API key.

**Why compute PAIRS_WITH at import time rather than per-query?** Style compatibility between items is static - it doesn't change per query. Pre-computing edges makes graph retrieval fast and deterministic.

**Why no image processing despite having image_path?** Photo upload with vision model is a future enhancement. The `image_path` column is in the schema now so data doesn't need to be reimported later.

**Why a single user?** Wardrobe is inherently personal. The `user_id` field stays in the schema for forward compatibility, but the system is designed and tuned for one person's data.
