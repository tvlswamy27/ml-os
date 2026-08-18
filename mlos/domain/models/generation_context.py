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

    @property
    def problem_type(self) -> str | None:
        if self.project_memory.dataset and self.project_memory.dataset.problem_type:
            return self.project_memory.dataset.problem_type
        if self.project_memory.project_profile:
            return self.project_memory.project_profile.problem_type
        return None

    @property
    def target_column(self) -> str | None:
        if self.project_memory.dataset:
            return self.project_memory.dataset.target
        return None

    @property
    def selected_features(self) -> list[str]:
        if not self.project_memory.dataset:
            return []
        ds = self.project_memory.dataset
        all_cols = ds.numerical_columns + ds.categorical_columns
        # Return all features except target
        return [c for c in all_cols if c != ds.target]

