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
        context,
    ) -> list[Decision]:
        from mlos.domain.models.decision_context import DecisionContext

        decisions: list[Decision] = []

        active_rule = self.get_active_rule(context, "scaling")
        if active_rule:
            strategy = active_rule.parameters.get("strategy")
            if strategy:
                decisions.append(
                    Decision(
                        title="Scaling Strategy: global",
                        strategy=strategy,
                        confidence=f"{active_rule.confidence_score * 100:.0f}%",
                        reason=f"Overridden by active knowledge rule (version {active_rule.version_number}).",
                    )
                )

        return decisions
