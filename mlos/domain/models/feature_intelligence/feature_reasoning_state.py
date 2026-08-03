"""
FeatureReasoningState domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.feature_intelligence.feature_profile import FeatureProfile
from mlos.domain.models.feature_intelligence.relationship_profile import (
    RelationshipProfile,
)
from mlos.domain.models.feature_intelligence.ranking_profile import RankingProfile


@dataclass(frozen=True)
class FeatureReasoningState:
    """
    Immutable reasoning facts for Feature Intelligence stages.
    """

    feature_profiles: dict[str, FeatureProfile] = field(default_factory=dict)
    relationship_profile: RelationshipProfile = field(
        default_factory=RelationshipProfile
    )
    ranking_profile: RankingProfile = field(default_factory=RankingProfile)
    target_leakage_candidates: tuple[str, ...] = field(default_factory=tuple)
    facts: dict[str, str] = field(default_factory=dict)
