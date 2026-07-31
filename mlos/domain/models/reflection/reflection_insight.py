"""
ReflectionInsight domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReflectionInsight:
    """
    Standardized abstraction for any reasoning observation or pattern.
    Represents observations only (no recommendation fields).
    """

    insight_id: str
    insight_type: str  # "SUCCESS", "FAILURE", "REGRESSION", "METRIC_TREND"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    summary: str
    evidence: tuple[str, ...]
    confidence: float
