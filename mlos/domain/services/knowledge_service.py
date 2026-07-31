from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.knowledge.knowledge_context import (
    KnowledgeContext,
    LearningSummary,
    LearningUpdateSummary,
    KnowledgeSummary,
)
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.knowledge.knowledge_engine import KnowledgeEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService


class KnowledgeService:
    """
    Coordinates context building, execution, and persistence of KnowledgeSessions.
    """

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.knowledge_engine = knowledge_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> KnowledgeContext:
        """
        Translates raw ProjectMemory historical sessions into window-constrained summaries.
        """
        # Build existing knowledge summary representing active entries
        knowledge_summary = KnowledgeSummary(
            active_entries=tuple(memory.knowledge_entries)
        )

        # Map learning sessions to summaries
        learning_summaries = []
        for l in memory.learning_sessions:
            updates = tuple(
                LearningUpdateSummary(
                    update_id=u.update_id,
                    update_type=u.update_type.value,
                    target_subsystem=u.target_subsystem,
                    target_component=u.target_component,
                    parameters=dict(u.parameters),
                    confidence_score=l.confidence.score if l.confidence else 0.5,
                    evidence_observations=(
                        u.evidence.supporting_observations if u.evidence else ()
                    ),
                )
                for u in l.updates
            )
            learning_summaries.append(
                LearningSummary(
                    session_id=str(l.id),
                    updates=updates,
                    confidence_accepted=(
                        l.confidence.accepted if l.confidence else False
                    ),
                )
            )

        latest_learning = learning_summaries[-1] if learning_summaries else None
        hist_learnings = learning_summaries[:-1] if learning_summaries else []

        return KnowledgeContext(
            project_name=memory.project_name,
            project_goal=memory.project_goal,
            latest_learning=latest_learning,
            historical_learnings=tuple(hist_learnings),
            existing_knowledge=knowledge_summary,
        )

    def run_knowledge(self, context: KnowledgeContext) -> KnowledgeSession:
        """Invokes the stateless KnowledgeEngine on the context."""
        return self.knowledge_engine.manage(context)

    def manage(self, memory: ProjectMemory) -> KnowledgeSession:
        """Orchestrates building context, running management, and persisting results."""
        from datetime import datetime

        # Update usage metrics for all existing knowledge entries
        for entry in memory.knowledge_entries:
            matched_sessions = []
            entry_naive = (
                entry.created_at.replace(tzinfo=None)
                if entry.created_at
                else datetime.min
            )
            for ps in memory.planning_sessions:
                ps_naive = (
                    ps.created_at.replace(tzinfo=None)
                    if ps.created_at
                    else datetime.min
                )
                if ps_naive > entry_naive:
                    matched_sessions.append(ps)

            if matched_sessions:
                count = len(matched_sessions)
                latest_sess = matched_sessions[-1]
                object.__setattr__(entry, "usage_count", count)
                object.__setattr__(entry, "last_used", latest_sess.created_at)
                sub = entry.target_subsystem
                object.__setattr__(entry, "usage_metadata", {"subsystems": sub})
            else:
                object.__setattr__(entry, "usage_count", 0)
                object.__setattr__(entry, "last_used", None)
                object.__setattr__(entry, "usage_metadata", {})

        context = self.build_context(memory)
        session = self.run_knowledge(context)
        self.project_memory_service.add_knowledge_session(memory, session)
        return session
