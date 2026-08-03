"""
FeatureEngineeringProposal domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.models.feature_intelligence.feature_confidence import FeatureConfidence
from mlos.domain.models.feature_intelligence.feature_lineage import FeatureLineage


@dataclass(frozen=True)
class FeatureEngineeringProposal:
    """
    Dedicated model proposing feature engineering transformations.
    """

    proposal_id: str
    source_columns: tuple[str, ...]
    generated_feature: str
    transformation: str
    expected_gain: float  # Expected feature importance or metrics gain
    computational_cost: str  # 'LOW', 'MEDIUM', 'HIGH'
    confidence: FeatureConfidence
    lineage: FeatureLineage | None = None
