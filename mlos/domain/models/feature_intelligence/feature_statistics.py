"""
FeatureStatistics domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureStatistics:
    """
    Consolidated statistics for a dataset feature column.
    """

    missing_percentage: float
    variance: float
    skewness: float
    kurtosis: float
    entropy: float
    uniqueness_ratio: float
    duplicate_ratio: float
    outlier_percentage: float
