"""
Scaling Decision.

Generates feature scaling decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.decision import Decision


class ScalingDecision(BaseStrategy):

    def decide(
        self,
        context,
    ) -> list[Decision]:
        from mlos.domain.models.decision_context import DecisionContext

        if isinstance(context, DecisionContext):
            memory = context.project_memory
        else:
            memory = context

        decisions: list[Decision] = []
        dataset = memory.dataset

        if dataset is None:
            return decisions

        active_rule = self.get_active_rule(context, "scaling")
        strategy = None
        confidence = "High"
        reason = ""

        if active_rule:
            strategy = active_rule.parameters.get("strategy")
            if strategy:
                reason = f"Overridden by active knowledge rule (version {active_rule.version_number})."
                confidence = f"{active_rule.confidence_score * 100:.0f}%"

        if not strategy:
            num_cols = [c for c in dataset.numerical_columns if c != dataset.target]
            if num_cols:
                strategy = "StandardScaler"
                confidence = "High"
                reason = f"Scale numerical features {num_cols} using StandardScaler."

        if strategy:
            num_cols = [c for c in dataset.numerical_columns if c != dataset.target]
            decisions.append(
                Decision(
                    title="Scaling Strategy: global",
                    strategy=strategy,
                    confidence=confidence,
                    reason=reason,
                    columns=num_cols,
                )
            )

        return decisions
