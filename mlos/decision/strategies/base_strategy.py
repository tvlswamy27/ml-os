"""
Base strategy.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision
from mlos.domain.models.decision_context import DecisionContext


class BaseStrategy(ABC):
    """
    Base class for all decision strategies.
    """

    @abstractmethod
    def decide(
        self,
        context: DecisionContext,
    ) -> list[Decision]:
        """
        Generate decisions.
        """
        pass

    def get_active_rule(self, context, component_name: str):
        """
        Retrieves the active rule summary for this strategy if it exists.
        """
        from mlos.domain.models.decision_context import DecisionContext

        if isinstance(context, DecisionContext):
            for rule in context.knowledge_summary.rules:
                if rule.subsystem == "decision" and rule.component in (
                    component_name,
                    self.__class__.__name__,
                ):
                    return rule
        return None


from abc import ABC, abstractmethod


class DecisionStrategy(ABC):

    @abstractmethod
    def decide(
        self,
        context,
    ):
        pass
