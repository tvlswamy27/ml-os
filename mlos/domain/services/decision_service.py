"""
Decision Service.

Translates ProjectMemory to DecisionContext and orchestrates the decision flow.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision
from mlos.domain.models.decision_context import DecisionContext
from mlos.decision.decision_engine import DecisionEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService


class DecisionService:
    """
    Coordinates building decision contexts, executing decision engines, and persisting results.
    """

    def __init__(
        self,
        decision_engine: DecisionEngine,
        project_memory_service: ProjectMemoryService,
    ):
        """
        Initialize with injected dependencies.
        """
        self.decision_engine = decision_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> DecisionContext:
        """
        Translate ProjectMemory into an immutable DecisionContext.
        """
        strategy = None
        if memory.planning_sessions:
            latest_session = memory.planning_sessions[-1]
            strategy = latest_session.selected_execution_strategy

        from mlos.domain.models.knowledge_summary import build_knowledge_summary

        return DecisionContext(
            project_memory=memory,
            execution_strategy=strategy,
            knowledge_summary=build_knowledge_summary(memory),
        )

    def run_decisions(self, context: DecisionContext) -> list[Decision]:
        """
        Accept only a DecisionContext, invoke the DecisionEngine, and return decisions.
        """
        return self.decision_engine.decide(context)

    def decide(self, memory: ProjectMemory) -> list[Decision]:
        """
        Orchestrate the complete decision flow.
        """
        context = self.build_context(memory)
        decisions = self.run_decisions(context)
        self.project_memory_service.update_decisions(memory, decisions)
        return decisions
