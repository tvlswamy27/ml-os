"""
Train/Test Split Decision.

Generates train/test split decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision

class TrainTestSplitDecision(BaseStrategy):

    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:

        return [
            Decision(
                title="Train/Test Split",
                strategy="80/20 Split",
                confidence="High",
                reason="80/20 is a good default split for supervised learning.",
            )
        ]
