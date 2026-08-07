"""
GenerationContext domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.models.decision import Decision
from mlos.domain.models.project_memory import ProjectMemory


@dataclass(frozen=True)
class GenerationContext:
    """
    Immutable input context for the Generation Engine.
    """

    project_memory: ProjectMemory
    decisions: tuple[Decision, ...]
