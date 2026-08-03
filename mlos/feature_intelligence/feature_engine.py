"""
FeatureEngine core orchestrator.

Author: Antigravity
License: MIT
"""

import pandas as pd
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.feature_intelligence.algorithms.feature_algorithm import FeatureAlgorithm


class FeatureEngine:
    """
    Orchestrator that delegates to an injected FeatureAlgorithm.
    """

    def __init__(self, feature_algorithm: FeatureAlgorithm | None = None):
        """
        Initialize with injected dependency.
        """
        if feature_algorithm is None:
            from mlos.feature_intelligence.algorithms.rule_based_feature_algorithm import (
                RuleBasedFeatureAlgorithm,
            )

            feature_algorithm = RuleBasedFeatureAlgorithm()
        self.feature_algorithm = feature_algorithm

    def analyze(
        self, context: FeatureContext, dataframe: pd.DataFrame
    ) -> FeatureSession:
        """
        Delegate analysis to the injected algorithm.
        """
        return self.feature_algorithm.analyze(context, dataframe)
