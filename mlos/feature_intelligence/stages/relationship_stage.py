"""
RelationshipAnalysisStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
import pandas as pd
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class RelationshipAnalysisStage(ABC):
    """
    Abstract interface for the Relationship Analysis cognitive stage.
    """

    @abstractmethod
    def analyze(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Analyzes multicollinearity, redundancies, correlations, and relationships with the target.
        """
        pass
