"""
FeatureRecommendation domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.enums.recommendation_action import RecommendationAction
from mlos.domain.models.feature_intelligence.feature_confidence import FeatureConfidence
from mlos.domain.models.feature_intelligence.recommendation_evidence import (
    RecommendationEvidence,
)


@dataclass(frozen=True)
class FeatureRecommendation:
    """
    Actionable feature selection recommendation.
    """

    recommendation_id: str
    action: RecommendationAction
    target_columns: tuple[str, ...]
    reasoning: str
    confidence: FeatureConfidence
    evidence: RecommendationEvidence = field(default_factory=RecommendationEvidence)
