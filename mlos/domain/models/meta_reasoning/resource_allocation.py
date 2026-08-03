"""
ResourceAllocation domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceAllocation:
    """
    Immutable representation of resource budgets and bounds allocated per subsystem.
    """

    token_budget: int | None = None
    cost_budget_usd: float | None = None
    reasoning_budget: int | None = None
    cpu_cores_limit: float | None = None
    memory_limit_mb: int | None = None
    cache_usage_limit_mb: int | None = None
    max_worker_limits: int | None = None
    additional_resources: dict[str, float] = field(default_factory=dict)
