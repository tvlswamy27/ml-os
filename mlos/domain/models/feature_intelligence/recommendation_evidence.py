"""
RecommendationEvidence domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecommendationEvidence:
    """
    Structured evidence explaining and reproducing a feature recommendation.
    """

    triggered_rules: tuple[str, ...] = field(default_factory=tuple)
    statistics_used: tuple[str, ...] = field(default_factory=tuple)
    thresholds: dict[str, float] = field(default_factory=dict)
    supporting_features: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
