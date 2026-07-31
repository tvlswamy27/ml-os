"""
ReflectionConfidence domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReflectionConfidence:
    """
    Richer confidence model including uncertainty and an acceptance threshold.
    """

    score: float  # 0.0 to 1.0
    uncertainty: float  # 0.0 to 1.0 (quantifies unknowns/metric variance)
    evidence: tuple[str, ...]  # Supporting session IDs or key observations
    explanation: str  # Detailed reasoning for confidence score
    accepted: bool  # Decided based on score and uncertainty threshold
