from dataclasses import dataclass, field
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry


@dataclass(frozen=True)
class LearningUpdateSummary:
    """Lightweight summary of a LearningUpdate proposal."""

    update_id: str
    update_type: str
    target_subsystem: str
    target_component: str
    parameters: dict[str, str]
    confidence_score: float
    evidence_observations: tuple[str, ...]


@dataclass(frozen=True)
class LearningSummary:
    """Lightweight summary of a LearningSession."""

    session_id: str
    updates: tuple[LearningUpdateSummary, ...]
    confidence_accepted: bool


@dataclass(frozen=True)
class KnowledgeSummary:
    """Lightweight representation of the current KnowledgeEntries."""

    active_entries: tuple[KnowledgeEntry, ...]


@dataclass(frozen=True)
class KnowledgeContext:
    """
    Input context containing windowed learning histories and existing active knowledge.
    Enforces decoupling boundaries to prevent tight subclass integration.
    """

    project_name: str
    project_goal: str
    latest_learning: LearningSummary | None
    historical_learnings: tuple[LearningSummary, ...] = field(default_factory=tuple)
    existing_knowledge: KnowledgeSummary | None = None
