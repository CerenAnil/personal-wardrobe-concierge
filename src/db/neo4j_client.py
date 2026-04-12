"""
Neo4j AuraDB client — lazy driver, Cypher wrapper.
Seeding and query patterns live in Phase 2.
"""

from __future__ import annotations

import os
from typing import Any

from neo4j import GraphDatabase, Driver

_driver: Driver | None = None


def _get_driver() -> Driver:
    global _driver
    if _driver is None:
        uri  = os.environ["NEO4J_URI"]
        user = os.environ["NEO4J_USER"]
        pwd  = os.environ["NEO4J_PASSWORD"]
        _driver = GraphDatabase.driver(uri, auth=(user, pwd))
    return _driver


def close() -> None:
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def run_query(cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
    """Execute a read Cypher query and return list of record dicts."""
    with _get_driver().session() as session:
        result = session.run(cypher, params or {})
        return [dict(r) for r in result]


def run_write(cypher: str, params: dict | None = None) -> None:
    """Execute a write Cypher statement inside a write transaction."""
    with _get_driver().session() as session:
        session.execute_write(lambda tx: tx.run(cypher, params or {}))
