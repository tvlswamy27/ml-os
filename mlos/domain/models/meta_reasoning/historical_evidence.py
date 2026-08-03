"""
HistoricalEvidence domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.meta_reasoning.execution_snapshot import ExecutionSnapshot


@dataclass(frozen=True)
class HistoricalEvidence:
    """
    Closed-loop evidence referencing past ExecutionSnapshot records.
    """

    snapshots: tuple[ExecutionSnapshot, ...] = field(default_factory=tuple)
    aggregated_accuracies: dict[str, float] = field(default_factory=dict)
    proven_rules: tuple[str, ...] = field(default_factory=tuple)
