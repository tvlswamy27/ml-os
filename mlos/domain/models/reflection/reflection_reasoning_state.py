"""
ReflectionReasoningState domain models and typed statistics helpers.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetricStats:
    """Statistical summary of a metric over historical runs."""

    mean: float
    std: float
    min_val: float
    max_val: float
    latest_val: float


@dataclass(frozen=True)
class ExecutionStats:
    """Aggregated stats about execution outcomes."""

    success_rate: float
    fail_count: int
    total_runs: int
    avg_duration: float


@dataclass(frozen=True)
class PlanningStats:
    """Aggregated stats about planning strategies chosen."""

    strategy_counts: dict[str, int] = field(default_factory=dict)
    most_frequent_strategy: str | None = None


@dataclass(frozen=True)
class TrendStats:
    """Trend analysis for a specific metric key."""

    metric_key: str
    direction: str  # "IMPROVING", "DEGRADING", "STABLE"
    slope: float
    history: tuple[float, ...]


@dataclass(frozen=True)
class ReflectionReasoningState:
    """
    Typed reasoning state built during Reflection.
    Carries structured, queryable analytics across reasoning phases.
    """

    metric_history: dict[str, tuple[float, ...]]  # metric_name -> historical values
    metrics_stats: dict[str, MetricStats]  # metric_name -> MetricStats
    execution_stats: ExecutionStats
    planning_stats: PlanningStats
    trend_stats: dict[str, TrendStats]  # metric_name -> TrendStats
    run_comparisons: tuple[dict, ...]  # pairwise delta records between runs
    baseline_metrics: dict[str, float]  # baseline metric scores
