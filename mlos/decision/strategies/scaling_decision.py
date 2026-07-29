"""
Scaling Decision.

Generates feature scaling decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision


class ScalingDecision(BaseStrategy):

    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:

        decisions = []

        return decisions
