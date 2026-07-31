from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.learning.learning_context import (
    LearningContext,
    ReflectionSummary,
    FeedbackSummary,
)
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.learning.learning_engine import LearningEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService


class LearningService:
    """
    Coordinates context building, execution, and persistence of LearningSessions.
    """

    def __init__(
        self,
        learning_engine: LearningEngine,
        project_memory_service: ProjectMemoryService,
        window_size: int | None = 10,
    ):
        self.learning_engine = learning_engine
        self.project_memory_service = project_memory_service
        self.window_size = window_size

    def build_context(self, memory: ProjectMemory) -> LearningContext:
        """
        Translates raw ProjectMemory reflection history into window-constrained ReflectionSummaries.
        """
        limit = self.window_size

        reflection_summaries = []
        for r in memory.reflection_sessions:
            feedback_summaries = tuple(
                FeedbackSummary(
                    feedback_id=f.feedback_id,
                    target_subsystem=f.target_subsystem,
                    target_component=f.target_component,
                    action_type=f.action_type,
                    parameters=dict(f.parameters),
                    priority=f.priority,
                    reason=f.reason,
                )
                for f in r.feedback
            )
            reflection_summaries.append(
                ReflectionSummary(
                    session_id=str(r.id),
                    summary=r.summary,
                    feedback=feedback_summaries,
                    confidence_accepted=(
                        r.confidence.accepted if r.confidence else False
                    ),
                )
            )

        # Slice summaries using window limit (latest is active, preceding are historical)
        hist_reflections = reflection_summaries[:-1] if reflection_summaries else []
        if limit is not None:
            hist_reflections = hist_reflections[-limit:]

        latest_reflection = reflection_summaries[-1] if reflection_summaries else None

        from mlos.domain.models.knowledge_summary import build_knowledge_summary

        return LearningContext(
            project_name=memory.project_name,
            project_goal=memory.project_goal,
            latest_reflection=latest_reflection,
            historical_reflections=tuple(hist_reflections),
            window_size=limit,
            knowledge_summary=build_knowledge_summary(memory),
        )

    def run_learning(self, context: LearningContext) -> LearningSession:
        """Invokes the stateless LearningEngine on the context."""
        return self.learning_engine.learn(context)

    def learn(self, memory: ProjectMemory) -> LearningSession:
        """Orchestrates building context, running learning, and persisting results."""
        context = self.build_context(memory)
        session = self.run_learning(context)
        self.project_memory_service.add_learning_session(memory, session)
        return session
