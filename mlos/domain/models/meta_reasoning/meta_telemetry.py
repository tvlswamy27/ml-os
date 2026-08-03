"""
MetaTelemetry domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetaTelemetry:
    """
    Orchestrator telemetry details.
    """

    provider: str
    model: str
    latency_ms: float
    fallback_used: bool
    tokens_used: int
    cost_usd: float
