"""
ExecutionPlan domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime

from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.execution_policy import ExecutionPolicy
from mlos.domain.models.meta_reasoning.execution_schedule import ExecutionSchedule
from mlos.domain.models.meta_reasoning.policy_version import PolicyVersion


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Immutable ExecutionPlan contract with checksum for validation, replay, and caching.
    """

    policy_version: PolicyVersion
    subsystem_policies: dict[SubsystemName, ExecutionPolicy]
    execution_schedule: ExecutionSchedule
    optimization_result: dict[str, float]
    planner_name: str
    planner_version: str
    generated_at: datetime
    checksum: str
