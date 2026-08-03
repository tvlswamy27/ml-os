"""
FeatureInsight domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeatureInsight:
    """
    Standardized representation of a key Feature Intelligence observation.
    """

    insight_id: str
    insight_type: str  # "TARGET_LEAKAGE", "MULTICOLLINEARITY", "HIGH_SKEWNESS", etc.
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    summary: str
    affected_columns: tuple[str, ...] = field(default_factory=tuple)
    value: float | None = None
    explanation: str = ""
