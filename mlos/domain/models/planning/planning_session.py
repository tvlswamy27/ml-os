"""
PlanningSession domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.base import BaseModel
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.observation import Observation
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class PlanningSession(BaseModel):  # type: ignore[misc]
    """
    Represents an immutable, single planning session iteration.
    """

    context: PlanningContext

    status: str

    observations: list[Observation] = field(default_factory=list)

    hypotheses: list[Hypothesis] = field(default_factory=list)

    candidates: list[CandidateStrategy] = field(default_factory=list)

    selected_execution_strategy: ExecutionStrategy | None = None

    telemetry: PlanningTelemetry | None = None


# Restore BaseModel to original non-frozen state for other subclasses
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
