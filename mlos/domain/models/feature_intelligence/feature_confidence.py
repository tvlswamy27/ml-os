"""
FeatureConfidence domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeatureConfidence:
    """
    Multi-dimensional confidence metrics for Feature Intelligence recommendations/proposals.
    """

    score: float  # Confidence score between 0.0 and 1.0
    uncertainty: float  # Uncertainty score between 0.0 and 1.0
    supporting_evidence: tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""
