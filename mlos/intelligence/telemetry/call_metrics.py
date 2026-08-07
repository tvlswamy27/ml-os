from dataclasses import dataclass
from datetime import datetime

from mlos.intelligence.telemetry.token_usage import TokenUsage


@dataclass(frozen=True)
class CallMetrics:
    """
    Immutable telemetry representing metadata about a single LLM API transaction.
    """

    request_id: str
    provider: str
    model: str
    latency_ms: float
    token_usage: TokenUsage | None
    cost: float
    cache_hit: bool
    timestamp: datetime
    error_message: str | None = None
