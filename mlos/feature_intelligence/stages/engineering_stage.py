"""
FeatureEngineeringStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

import pandas as pd

from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_engineering_proposal import (
    FeatureEngineeringProposal,
)
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class FeatureEngineeringStage(ABC):
    """
    Abstract interface for the Feature Engineering cognitive stage.
    """

    @abstractmethod
    def engineer(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> list[FeatureEngineeringProposal]:
        """
        Recommends candidates for polynomial, log, interaction, scaling, and encodings.
        """
