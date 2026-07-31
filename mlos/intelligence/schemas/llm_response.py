from dataclasses import dataclass
from typing import Any
from mlos.intelligence.telemetry.call_metrics import CallMetrics


@dataclass(frozen=True)
class LLMResponse:
    """
    Strongly typed immutable response payload from an intelligence provider call.
    """

    parsed_output: Any
    raw_response: str
    call_metrics: CallMetrics
    cache_hit: bool
    provider: str
    model: str
    latency: float
    cost: float
    retry_count: int
    validation_passed: bool
