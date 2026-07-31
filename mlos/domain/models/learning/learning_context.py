from dataclasses import dataclass, field


from mlos.domain.models.knowledge_summary import KnowledgeSummary


@dataclass(frozen=True)
class FeedbackSummary:
    """Lightweight representation of a ReflectionFeedback item."""

    feedback_id: str
    target_subsystem: str
    target_component: str
    action_type: str
    parameters: dict[str, str]
    priority: str
    reason: str


@dataclass(frozen=True)
class ReflectionSummary:
    """Lightweight representation of a ReflectionSession."""

    session_id: str
    summary: str
    feedback: tuple[FeedbackSummary, ...]
    confidence_accepted: bool


@dataclass(frozen=True)
class LearningContext:
    """
    Input context for the Learning Subsystem.
    Restricts access to Reflection summaries, enforcing decoupled boundaries.
    """

    project_name: str
    project_goal: str
    latest_reflection: ReflectionSummary | None
    historical_reflections: tuple[ReflectionSummary, ...] = field(default_factory=tuple)
    window_size: int | None = None
    knowledge_summary: KnowledgeSummary = field(default_factory=KnowledgeSummary)
