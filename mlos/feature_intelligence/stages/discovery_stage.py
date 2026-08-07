"""
FeatureDiscoveryStage abstract interface.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

import pandas as pd

from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class FeatureDiscoveryStage(ABC):
    """
    Abstract interface for the Feature Discovery cognitive stage.
    """

    @abstractmethod
    def discover(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Discovers datatypes, identifier columns, and target leakages.
        """
