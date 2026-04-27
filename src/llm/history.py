"""
In-memory LLM call log.

Stores the last MAX_ENTRIES calls across all agents.
Each entry captures the full request (system + user prompt),
the response text, token counts, latency, and estimated cost.

Reset on server restart — this is intentional (no persistence needed).
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime

MAX_ENTRIES = 100

PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80,  "output": 4.00},
    "claude-haiku-4-5":          {"input": 0.80,  "output": 4.00},
    "claude-sonnet-4-6":         {"input": 3.00,  "output": 15.00},
    # Local models are free
}


@dataclass
class LLMCall:
    id: int
    timestamp: str
    role: str              # "outfit" | "occasion" | "manager" | "unknown"
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    request: dict          # {"system": str, "user": str}
    response: str


_log: deque[LLMCall] = deque(maxlen=MAX_ENTRIES)
_counter: int = 0


def record(
    role: str,
    model: str,
    system: str,
    user: str,
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
) -> None:
    global _counter
    _counter += 1

    pricing = PRICE_TABLE.get(model, {"input": 0.0, "output": 0.0})
    cost_usd = (
        input_tokens  / 1_000_000 * pricing["input"] +
        output_tokens / 1_000_000 * pricing["output"]
    )

    _log.appendleft(LLMCall(
        id=_counter,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        role=role,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=round(latency_ms, 1),
        cost_usd=round(cost_usd, 6),
        request={"system": system, "user": user},
        response=response_text,
    ))


def get_all() -> list[dict]:
    return [asdict(entry) for entry in _log]


def clear() -> None:
    global _counter
    _log.clear()
    _counter = 0
