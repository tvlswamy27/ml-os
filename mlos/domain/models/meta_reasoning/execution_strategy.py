"""
ExecutionStrategy domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.enums.execution_mode import ExecutionMode
from mlos.domain.models.meta_reasoning.policies import (
    CachePolicy,
    RetryPolicy,
    ValidationPolicy,
)
from mlos.domain.models.meta_reasoning.provider_capability import ProviderCapability


@dataclass(frozen=True)
class ExecutionStrategy:
    """
    Immutable routing execution strategy for a subsystem.
    """

    algorithm_type: ExecutionMode  # RULE, LLM, HYBRID
    provider_selection: ProviderCapability | None
    cache_policy: CachePolicy
    validation_policy: ValidationPolicy
    retry_policy: RetryPolicy
