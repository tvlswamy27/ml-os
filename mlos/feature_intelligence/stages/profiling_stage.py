"""
FeatureProfilingStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
import pandas as pd
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class FeatureProfilingStage(ABC):
    """
    Abstract interface for the Feature Profiling cognitive stage.
    """

    @abstractmethod
    def profile(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Profiles variance, skewness, outliers, missing percentage, and uniqueness metrics.
        """
        pass
