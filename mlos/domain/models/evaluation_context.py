"""
EvaluationContext domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.execution_session import ExecutionSession


@dataclass(frozen=True)
class EvaluationContext:
    """
    Immutable input context for the Evaluation Engine.
    """

    project_memory: ProjectMemory
    execution_session: ExecutionSession | None
