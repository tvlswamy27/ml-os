"""
ReflectionContext domain models.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.knowledge_summary import KnowledgeSummary


@dataclass(frozen=True)
class PlanningSummary:
    """Lightweight representation of a PlanningSession to minimize coupling."""

    session_id: str
    selected_strategy: str | None
    planned_steps: tuple[str, ...]
    parameters: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionSummary:
    """Lightweight representation of an ExecutionSession to minimize coupling."""

    session_id: str
    status: str
    exit_code: int | None
    duration_seconds: float
    error_message: str | None


@dataclass(frozen=True)
class EvaluationSummary:
    """Lightweight representation of an EvaluationSession to minimize coupling."""

    session_id: str
    metrics: dict[str, float] = field(default_factory=dict)
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class ReflectionContext:
    """
    Input context containing only decoupled summaries.
    Protects subsystem boundaries and controls historical processing scope.
    """

    project_name: str
    project_goal: str

    latest_planning: PlanningSummary | None
    latest_execution: ExecutionSummary | None
    latest_evaluation: EvaluationSummary | None

    historical_plannings: tuple[PlanningSummary, ...] = field(default_factory=tuple)
    historical_executions: tuple[ExecutionSummary, ...] = field(default_factory=tuple)
    historical_evaluations: tuple[EvaluationSummary, ...] = field(default_factory=tuple)

    window_size: int | None = None
    knowledge_summary: KnowledgeSummary = field(default_factory=KnowledgeSummary)
