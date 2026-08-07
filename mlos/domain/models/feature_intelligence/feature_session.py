"""
FeatureSession domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_engineering_proposal import (
    FeatureEngineeringProposal,
)
from mlos.domain.models.feature_intelligence.feature_insight import FeatureInsight
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)
from mlos.domain.models.feature_intelligence.feature_recommendation import (
    FeatureRecommendation,
)

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class FeatureSession(BaseModel):  # type: ignore[misc]
    """
    Immutable representation of a single Feature Intelligence cycle.
    """

    context: FeatureContext
    reasoning_state: FeatureReasoningState
    insights: list[FeatureInsight] = field(default_factory=list)
    recommendations: list[FeatureRecommendation] = field(default_factory=list)
    engineering_proposals: list[FeatureEngineeringProposal] = field(
        default_factory=list
    )
    consensus_ranking: tuple[str, ...] = field(default_factory=tuple)
    status: str = "SUCCESS"


# Restore BaseModel to original non-frozen state for other subclasses
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
