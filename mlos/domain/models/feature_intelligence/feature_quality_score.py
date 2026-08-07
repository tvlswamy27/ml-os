"""
FeatureQualityScore domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.models.feature_intelligence.feature_confidence import FeatureConfidence


@dataclass(frozen=True)
class FeatureQualityScore:
    """
    Immutable score aggregating multiple dimensions of quality for a single feature.
    """

    overall_score: float  # Weighted aggregation of other quality sub-scores
    information_score: float  # Value based on variance/entropy
    stability_score: float  # Score penalizing missingness and high outlier counts
    redundancy_score: (
        float  # Score penalizing correlation/redundancy with other features
    )
    engineering_potential: (
        float  # Potential gains from non-linear transformation/imputation
    )
    confidence: FeatureConfidence
