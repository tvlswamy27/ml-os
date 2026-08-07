"""
Evaluation Service.

Translates ProjectMemory to EvaluationContext and orchestrates performance evaluation.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.evaluation_context import EvaluationContext
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.evaluation.evaluation_engine import EvaluationEngine


class EvaluationService:
    """
    Coordinates metrics extraction, context building, and chronological session persistence.
    """

    def __init__(
        self,
        evaluation_engine: EvaluationEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.evaluation_engine = evaluation_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> EvaluationContext:
        """
        Translate ProjectMemory into an immutable EvaluationContext.
        """
        execution_session = (
            memory.execution_sessions[-1] if memory.execution_sessions else None
        )
        return EvaluationContext(
            project_memory=memory, execution_session=execution_session
        )

    def run_evaluation(
        self, context: EvaluationContext | ProjectMemory
    ) -> EvaluationSession:
        """
        Accept only EvaluationContext, delegate to EvaluationEngine, and return EvaluationSession.
        Supports ProjectMemory backward compatibly.
        """
        if isinstance(context, ProjectMemory):
            # Legacy call: orchestrate and persist
            return self.evaluate(context)

        from typing import cast

        res = self.evaluation_engine.evaluate(context)
        return cast(EvaluationSession, res)

    def evaluate(self, memory: ProjectMemory) -> EvaluationSession:
        """
        Orchestrate the complete evaluation flow.
        """
        context = self.build_context(memory)
        session = self.run_evaluation(context)
        self.project_memory_service.add_evaluation_session(memory, session)
        return session
