"""
ExecutionConstraints domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionConstraints:
    """
    Immutable deployment constraints restricting cognitive orchestration logic.
    """

    max_cost: float
    max_tokens: int
    max_latency: float
    max_cpu: float
    max_memory: float
    minimum_quality: float
    maximum_retry_depth: int
    must_use_local_models: bool
    allow_network_calls: bool
    allow_parallel_execution: bool
