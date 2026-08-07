"""
PlanningContext domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.knowledge_summary import KnowledgeSummary
from mlos.domain.models.planning.assumption import Assumption
from mlos.domain.models.planning.constraint import Constraint
from mlos.domain.models.planning.goal import Goal
from mlos.domain.models.planning.observation import Observation


@dataclass(frozen=True)
class PlanningContext:
    """
    Input context provided to the Planning Subsystem containing only relevant information.
    """

    project_name: str

    goals: tuple[Goal, ...] = field(default_factory=tuple)

    constraints: tuple[Constraint, ...] = field(default_factory=tuple)

    observations: tuple[Observation, ...] = field(default_factory=tuple)

    assumptions: tuple[Assumption, ...] = field(default_factory=tuple)

    knowledge_summary: KnowledgeSummary = field(default_factory=KnowledgeSummary)
