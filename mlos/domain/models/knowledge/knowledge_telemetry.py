"""
KnowledgeTelemetry domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.run_context import RunContext


@dataclass(frozen=True)
class KnowledgeTelemetry:
    """
    Type-safe execution metrics for a single knowledge management cycle.
    """

    provider: str

    model: str

    latency_ms: float

    cache_hit: bool

    fallback_used: bool

    validation_passed: bool

    request_id: str = ""

    token_usage: dict[str, int] = field(default_factory=dict)

    estimated_cost: float = 0.0

    run_context: RunContext | None = None
