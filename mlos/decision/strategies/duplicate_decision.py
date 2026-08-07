"""
Duplicate Decision.

Generates duplicate row decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.decision import Decision


class DuplicateDecision(BaseStrategy):

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

        active_rule = self.get_active_rule(context, "duplicate")
        if active_rule:
            strategy = active_rule.parameters.get("strategy")
            if strategy:
                decisions.append(
                    Decision(
                        title="Duplicate Row Strategy",
                        strategy=strategy,
                        confidence=f"{active_rule.confidence_score * 100:.0f}%",
                        reason=f"Overridden by active knowledge rule (version {active_rule.version_number}).",
                    )
                )
                return decisions

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
