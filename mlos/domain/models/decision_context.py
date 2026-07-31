"""
DecisionContext domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.knowledge_summary import KnowledgeSummary


@dataclass(frozen=True)
class DecisionContext:
    """
    Immutable input context for the Decision Engine.
    """

    project_memory: ProjectMemory
    execution_strategy: ExecutionStrategy | None = None
    knowledge_summary: KnowledgeSummary = field(default_factory=KnowledgeSummary)
