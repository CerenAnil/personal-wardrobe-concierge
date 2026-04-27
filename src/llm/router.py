"""
Model router — maps agent roles to model identifiers.

Reads from environment variables so routing is swappable without code changes.

Defaults (all fall back to WORKER_MODEL, which defaults to claude-haiku):
  OUTFIT_MODEL   - model used by the outfit selection agent
  OCCASION_MODEL - model used by the occasion reasoner agent
  MANAGER_MODEL  - model used by the manager agent

To route the outfit agent to LM Studio instead of Haiku, set:
  OUTFIT_MODEL=qwen/qwen3.5-9b

To route everything to LM Studio:
  OUTFIT_MODEL=qwen/qwen3.5-9b
  OCCASION_MODEL=qwen/qwen3.5-9b
"""

from __future__ import annotations

import os

_WORKER_DEFAULT  = "claude-haiku-4-5-20251001"
_MANAGER_DEFAULT = "claude-sonnet-4-6"

# Runtime overrides — set via API without restarting the server
_runtime_overrides: dict[str, str] = {}


def set_model(role: str, model: str) -> None:
    """Override the model for a role at runtime (survives until next server restart)."""
    _runtime_overrides[role] = model


def get_model(role: str) -> str:
    """
    Return the model identifier for the given agent role.

    Roles: "outfit" | "occasion" | "manager"
    """
    # Runtime overrides take precedence over env vars
    if role in _runtime_overrides:
        return _runtime_overrides[role]

    worker = os.getenv("WORKER_MODEL", _WORKER_DEFAULT)

    mapping = {
        "outfit":   os.getenv("OUTFIT_MODEL",   worker),
        "occasion": os.getenv("OCCASION_MODEL", worker),
        "manager":  os.getenv("MANAGER_MODEL",  _MANAGER_DEFAULT),
    }

    return mapping.get(role, worker)


def describe_routing() -> dict[str, str]:
    """Return the full current routing table (useful for logging/benchmarks)."""
    return {role: get_model(role) for role in ("outfit", "occasion", "manager")}
