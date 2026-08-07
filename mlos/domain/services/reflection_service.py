"""
Reflection Service.

Translates ProjectMemory to ReflectionContext and orchestrates the reflection flow.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.reflection.reflection_context import (
    EvaluationSummary,
    ExecutionSummary,
    PlanningSummary,
    ReflectionContext,
)
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.reflection.reflection_engine import ReflectionEngine


class ReflectionService:
    """
    Coordinates building reflection contexts, executing algorithms, and persisting results.
    """

    def __init__(
        self,
        reflection_engine: ReflectionEngine,
        project_memory_service: ProjectMemoryService,
        window_size: int | None = 10,
    ):
        """
        Initialize with injected dependencies.
        """
        self.reflection_engine = reflection_engine
        self.project_memory_service = project_memory_service
        self.window_size = window_size

    def build_context(self, memory: ProjectMemory) -> ReflectionContext:
        """
        Translate ProjectMemory into a decoupled, window-constrained ReflectionContext.
        """
        limit = self.window_size

        # 1. Map Planning Sessions to summaries
        planning_summaries = []
        for p in memory.planning_sessions:
            planning_summaries.append(
                PlanningSummary(
                    session_id=str(p.id),
                    selected_strategy=(
                        p.selected_execution_strategy.strategy_name
                        if p.selected_execution_strategy
                        else None
                    ),
                    planned_steps=(
                        tuple(p.selected_execution_strategy.topological_steps)
                        if p.selected_execution_strategy
                        else ()
                    ),
                    parameters={},
                )
            )

        # 2. Map Execution Sessions to summaries
        execution_summaries = []
        for e in memory.execution_sessions:
            execution_summaries.append(
                ExecutionSummary(
                    session_id=str(e.id),
                    status=e.status,
                    exit_code=e.exit_code,
                    duration_seconds=e.duration_seconds,
                    error_message=e.stderr if e.status == "FAILED" else None,
                )
            )

        # 3. Map Evaluation Sessions to summaries
        evaluation_summaries = []
        for v in memory.evaluation_sessions:
            evaluation_summaries.append(
                EvaluationSummary(
                    session_id=str(v.id),
                    metrics=v.metrics,
                    checks=v.checks,
                )
            )

        # Separate latest summaries from the historical summaries
        latest_planning = planning_summaries[-1] if planning_summaries else None
        latest_execution = execution_summaries[-1] if execution_summaries else None
        latest_evaluation = evaluation_summaries[-1] if evaluation_summaries else None

        # Slices history (excluding the latest run which is currently active)
        hist_planning = planning_summaries[:-1] if planning_summaries else []
        hist_execution = execution_summaries[:-1] if execution_summaries else []
        hist_evaluation = evaluation_summaries[:-1] if evaluation_summaries else []

        if limit is not None:
            hist_planning = hist_planning[-limit:]
            hist_execution = hist_execution[-limit:]
            hist_evaluation = hist_evaluation[-limit:]

        from mlos.domain.models.knowledge_summary import build_knowledge_summary

        return ReflectionContext(
            project_name=memory.project_name,
            project_goal=memory.project_goal,
            latest_planning=latest_planning,
            latest_execution=latest_execution,
            latest_evaluation=latest_evaluation,
            historical_plannings=tuple(hist_planning),
            historical_executions=tuple(hist_execution),
            historical_evaluations=tuple(hist_evaluation),
            window_size=limit,
            knowledge_summary=build_knowledge_summary(memory),
        )

    def run_reflection(self, context: ReflectionContext) -> ReflectionSession:
        """
        Accept only a ReflectionContext, invoke the ReflectionEngine, and return a ReflectionSession.
        """
        return self.reflection_engine.reflect(context)

    def reflect(self, memory: ProjectMemory) -> ReflectionSession:
        """
        Orchestrate the complete reflection flow.
        """
        context = self.build_context(memory)
        session = self.run_reflection(context)
        self.project_memory_service.add_reflection_session(memory, session)
        return session
