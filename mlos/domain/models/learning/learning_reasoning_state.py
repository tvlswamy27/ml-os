from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeedbackStats:
    """Aggregated statistics of reflection feedback items."""

    total_feedback_count: int
    priority_counts: dict[str, int]
    subsystem_counts: dict[str, int]


@dataclass(frozen=True)
class ActionStats:
    """Identifies frequency patterns and repeated outcomes."""

    action_frequencies: dict[str, int]
    repeated_failures: tuple[str, ...]
    repeated_successes: tuple[str, ...]


@dataclass(frozen=True)
class LearningTrendStats:
    """Traces historical trends of acceptance rates."""

    acceptance_history: tuple[bool, ...]
    stable_rate: float


@dataclass(frozen=True)
class LearningReasoningState:
    """
    Typed reasoning state carrying compiled stats across learning phases.
    """

    feedback_stats: FeedbackStats
    action_stats: ActionStats
    trend_stats: LearningTrendStats
    candidate_updates: tuple[dict, ...] = field(default_factory=tuple)
