"""
Decision Engine.

Generates ML decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision
from mlos.decision.strategies.missing_value_strategy import MissingValueStrategy

class DecisionEngine:
    """
    Makes preprocessing and modeling decisions.
    """
    def __init__(self):
        self.strategies = [
            MissingValueStrategy(),
        ]

    def decide(
        self,
        memory,
    ):

        decisions = []

        for strategy in self.strategies:
            decisions.extend(
                strategy.decide(memory)
            )

        return decisions
