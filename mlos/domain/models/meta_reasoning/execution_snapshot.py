"""
ExecutionSnapshot domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.models.meta_reasoning.policy_version import PolicyVersion
from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.execution_schedule import ExecutionSchedule
from mlos.domain.models.meta_reasoning.meta_telemetry import MetaTelemetry


@dataclass(frozen=True)
class ExecutionSnapshot:
    """
    Immutable representation of an execution session run snapshot.
    """

    run_id: UUID
    policy_version: PolicyVersion
    execution_plan: ExecutionPlan
    execution_schedule: ExecutionSchedule
    execution_state_history: tuple[tuple[datetime, ExecutionLifecycle], ...]
    telemetry: tuple[MetaTelemetry, ...]
    input_hash: str
    output_hash: str
    timestamps: dict[str, datetime] = field(default_factory=dict)
