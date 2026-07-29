"""
Decision Engine.

Generates ML decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision
from mlos.decision.strategies.missing_value_decision import MissingValueDecision
from mlos.decision.strategies.encoding_decision import EncodingDecision
from mlos.decision.strategies.scaling_decision import ScalingDecision
from mlos.decision.strategies.duplicate_decision import DuplicateDecision
from mlos.decision.strategies.train_test_split_decision import TrainTestSplitDecision

class DecisionEngine:
    """
    Makes preprocessing and modeling decisions.
    """
    def __init__(self):
        self.strategies = [
            MissingValueDecision(),
            EncodingDecision(),
            ScalingDecision(),
            DuplicateDecision(),
            TrainTestSplitDecision(),
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
