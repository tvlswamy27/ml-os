"""
RankingStrategy abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
import pandas as pd
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class RankingStrategy(ABC):
    """
    Abstract interface for pluggable feature ranking strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name of the ranking strategy.
        """
        pass

    @abstractmethod
    def score_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> dict[str, float]:
        """
        Compute feature importance scores. Higher values signify more important features.
        """
        pass
