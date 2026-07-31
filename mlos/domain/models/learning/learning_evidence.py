from dataclasses import dataclass, field


@dataclass(frozen=True)
class LearningEvidence:
    """
    Immutable explainability details backing a generated LearningUpdate.
    Provides complete traceability for audit logs, visualizers, and other subsystems.
    """

    reflection_session_ids: tuple[str, ...] = field(default_factory=tuple)
    evaluation_session_ids: tuple[str, ...] = field(default_factory=tuple)
    execution_session_ids: tuple[str, ...] = field(default_factory=tuple)
    metrics_used: tuple[str, ...] = field(default_factory=tuple)
    confidence_values: tuple[float, ...] = field(default_factory=tuple)
    frequency_counts: dict[str, int] = field(default_factory=dict)
    trend_information: dict[str, str] = field(default_factory=dict)
    supporting_observations: tuple[str, ...] = field(default_factory=tuple)
