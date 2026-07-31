"""
Encoding Strategy.

Generates encoding decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision


class EncodingDecision(BaseStrategy):

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

        active_rule = self.get_active_rule(context, "encoding")

        for column in dataset.categorical_columns:
            unique_count = dataset.unique_values.get(column)

            if unique_count is None:
                continue

            strategy = None
            confidence = "High"
            reason = ""
            if active_rule:
                strategy = active_rule.parameters.get(
                    column
                ) or active_rule.parameters.get("strategy")
                if strategy:
                    reason = f"Overridden by active knowledge rule (version {active_rule.version_number})."
                    confidence = f"{active_rule.confidence_score * 100:.0f}%"

            if not strategy:
                if unique_count <= 10:
                    strategy = "One-Hot Encoding"
                    confidence = "High"
                    reason = f"{column} has only {unique_count} unique values."
                else:
                    strategy = "Label Encoding"
                    confidence = "Medium"
                    reason = f"{column} has {unique_count} unique values."

            decisions.append(
                Decision(
                    title=f"Encoding Strategy: {column}",
                    strategy=strategy,
                    confidence=confidence,
                    reason=reason,
                )
            )

        return decisions
