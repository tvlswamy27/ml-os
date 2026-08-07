"""
FeatureSelectionStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)
from mlos.domain.models.feature_intelligence.feature_recommendation import (
    FeatureRecommendation,
)
from mlos.domain.models.feature_intelligence.ranking_profile import RankingProfile


class FeatureSelectionStage(ABC):
    """
    Abstract interface for the Feature Selection cognitive stage.
    """

    @abstractmethod
    def select(
        self,
        context: FeatureContext,
        ranking: RankingProfile,
        state: FeatureReasoningState,
    ) -> list[FeatureRecommendation]:
        """
        Formulates selection recommendations (KEEP, REMOVE, etc.) with reasoning and confidence evidence.
        """
