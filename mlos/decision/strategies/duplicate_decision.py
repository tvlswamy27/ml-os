"""
Duplicate Decision.

Generates duplicate row decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision


class DuplicateDecision(BaseStrategy):

    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:

        decisions: list[Decision] = []
        dataset = memory.dataset

        if dataset is None:
            return decisions

        if dataset.duplicate_rows > 0:
            decisions.append(
                Decision(
                    title="Duplicate Row Strategy",
                    strategy="Remove Duplicate Rows",
                    confidence="High",
                    reason=f"Dataset has {dataset.duplicate_rows} duplicate rows detected.",
                )
            )

        return decisions
