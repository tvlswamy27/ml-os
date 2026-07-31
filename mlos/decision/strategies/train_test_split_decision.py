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
        context,
    ) -> list[Decision]:
        from mlos.domain.models.decision_context import DecisionContext

        active_rule = self.get_active_rule(context, "split")
        if active_rule:
            strategy = active_rule.parameters.get(
                "strategy"
            ) or active_rule.parameters.get("test_size")
            if strategy:
                return [
                    Decision(
                        title="Train/Test Split",
                        strategy=strategy,
                        confidence=f"{active_rule.confidence_score * 100:.0f}%",
                        reason=f"Overridden by active knowledge rule (version {active_rule.version_number}).",
                    )
                ]

        if isinstance(context, DecisionContext):
            memory = context.project_memory
        else:
            memory = context

        return [
            Decision(
                title="Train/Test Split",
                strategy="80/20 Split",
                confidence="High",
                reason="80/20 is a good default split for supervised learning.",
            )
        ]
