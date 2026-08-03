"""
FeatureRankingStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
import pandas as pd
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)
from mlos.domain.models.feature_intelligence.ranking_profile import RankingProfile


class FeatureRankingStage(ABC):
    """
    Abstract interface for the Feature Ranking cognitive stage.
    """

    @abstractmethod
    def rank(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> RankingProfile:
        """
        Calculates individual rankings and builds consensus ranking via RRF.
        """
        pass
