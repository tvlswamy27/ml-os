"""
Decision Engine.

Generates ML decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.duplicate_decision import DuplicateDecision
from mlos.decision.strategies.encoding_decision import EncodingDecision
from mlos.decision.strategies.missing_value_decision import MissingValueDecision
from mlos.decision.strategies.scaling_decision import ScalingDecision
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
        context,
    ):
        """
        Generate decisions using the registered strategies, constrained by the execution strategy.
        """
        from mlos.domain.models.decision_context import DecisionContext

        if isinstance(context, DecisionContext):
            decision_ctx = context
        else:
            decision_ctx = DecisionContext(project_memory=context)

        decisions = []
        strategy_steps = {
            MissingValueDecision: "impute",
            EncodingDecision: "encode",
            ScalingDecision: "scale",
            DuplicateDecision: "duplicate",
            TrainTestSplitDecision: "split",
        }

        # Retrieve selected strategy steps if available
        allowed_steps = None
        if decision_ctx.execution_strategy is not None:
            allowed_steps = set(decision_ctx.execution_strategy.topological_steps)

        for strategy in self.strategies:
            step_name = strategy_steps.get(type(strategy))
            # If constrained by execution strategy, check if the step is allowed
            if allowed_steps is not None and step_name is not None:
                if step_name not in allowed_steps:
                    continue

            decisions.extend(strategy.decide(decision_ctx))

        return decisions
