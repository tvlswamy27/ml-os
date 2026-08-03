"""
FeatureProfile domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.enums.feature_type import FeatureType
from mlos.domain.models.feature_intelligence.feature_statistics import FeatureStatistics
from mlos.domain.models.feature_intelligence.feature_quality_score import (
    FeatureQualityScore,
)


@dataclass(frozen=True)
class FeatureProfile:
    """
    Strongly-typed profile representing analyzed characteristics of a feature column.
    """

    column_name: str
    feature_type: FeatureType
    statistics: FeatureStatistics
    quality_score: FeatureQualityScore
    is_constant: bool
    is_duplicate: bool
    is_identifier: bool
    cardinality: int
