"""
Unified LLM client.

Dispatches to the right backend based on model name:
  - "claude-*"  -> Anthropic SDK
  - anything else -> OpenAI-compatible endpoint (LM Studio at localhost:1234)

Usage:
    from src.llm.client import chat

    text = chat(
        model="claude-haiku-4-5-20251001",
        system="You are a stylist.",
        user="Pick an outfit.",
        max_tokens=1024,
    )
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import anthropic
import openai as openai_lib

from src.llm import history as llm_history

# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------
_anthropic_client: anthropic.Anthropic | None = None
_openai_client: openai_lib.OpenAI | None = None

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")


def _get_anthropic() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic()
    return _anthropic_client


def _get_openai() -> openai_lib.OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = openai_lib.OpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key="lm-studio",   # LM Studio ignores this but the SDK requires it
            timeout=200.0,         # ~200s covers 1500-tok output at 12 tok/s on consumer hardware
        )
    return _openai_client


# ---------------------------------------------------------------------------
# Response dataclass (normalised across backends)
# ---------------------------------------------------------------------------
@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def chat(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 1024,
    role: str = "unknown",
) -> str:
    """Convenience wrapper - returns just the text string."""
    return chat_full(model, system, user, max_tokens, role=role).text


def chat_full(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 1024,
    role: str = "unknown",
) -> LLMResponse:
    """Full response including token counts and latency (used by benchmark)."""
    t0 = time.perf_counter()

    if model.startswith("claude-"):
        response = _get_anthropic().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text          = response.content[0].text
        input_tokens  = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

    else:
        # OpenAI-compatible — LM Studio, Ollama, Together.ai, etc.
        response = _get_openai().chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system",  "content": system},
                {"role": "user",    "content": user},
            ],
        )
        text          = response.choices[0].message.content or ""
        input_tokens  = response.usage.prompt_tokens     if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

    latency_ms = (time.perf_counter() - t0) * 1000

    llm_history.record(
        role=role,
        model=model,
        system=system,
        user=user,
        response_text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )

    return LLMResponse(
        text=text,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )
