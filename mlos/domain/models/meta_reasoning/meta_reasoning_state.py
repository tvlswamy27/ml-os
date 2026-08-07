"""
MetaReasoningState domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.policy_diff import PolicyDiff


@dataclass(frozen=True)
class MetaReasoningState:
    """
    State tracking intermediate planner routing decisions.
    """

    execution_plan: ExecutionPlan | None = None
    optimization_objective_scores: dict[str, float] = field(default_factory=dict)
    diff_from_parent: PolicyDiff | None = None
    facts: dict[str, str] = field(default_factory=dict)
