"""
FeatureAlgorithm abstract base class.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

import pandas as pd

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
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.domain.models.feature_intelligence.ranking_profile import RankingProfile


class FeatureAlgorithm(ABC):
    """
    Template Method pattern base class for Feature Intelligence algorithms.
    """

    @abstractmethod
    def can_analyze(self, context: FeatureContext) -> bool:
        """
        Determine if this algorithm can run on the provided context.
        """

    def analyze(
        self, context: FeatureContext, dataframe: pd.DataFrame
    ) -> FeatureSession:
        """
        Template Method: Coordinates the modular cognitive stages of Feature Intelligence.
        """
        state = FeatureReasoningState()

        # Phase 1: Feature Discovery
        self._discover_features(context, dataframe, state)

        # Phase 2: Feature Profiling
        self._profile_features(context, dataframe, state)

        # Phase 3: Relationship Analysis
        self._analyze_relationships(context, dataframe, state)

        # Generate insights from findings
        insights = self._generate_insights(context, state)

        # Phase 4: Feature Ranking
        ranking_profile = self._rank_features(context, dataframe, state)

        # Phase 5: Feature Engineering
        proposals = self._recommend_engineering(context, dataframe, state)

        # Phase 6: Feature Selection
        recommendations = self._select_features(context, ranking_profile, state)

        # Construct and return final session DTO
        return self._construct_session(
            context=context,
            state=state,
            insights=insights,
            recommendations=recommendations,
            proposals=proposals,
            ranking_profile=ranking_profile,
        )

    @abstractmethod
    def _discover_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        pass

    @abstractmethod
    def _profile_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        pass

    @abstractmethod
    def _analyze_relationships(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        pass

    @abstractmethod
    def _generate_insights(
        self,
        context: FeatureContext,
        state: FeatureReasoningState,
    ) -> list[FeatureInsight]:
        pass

    @abstractmethod
    def _rank_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> RankingProfile:
        pass

    @abstractmethod
    def _recommend_engineering(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> list[FeatureEngineeringProposal]:
        pass

    @abstractmethod
    def _select_features(
        self,
        context: FeatureContext,
        ranking: RankingProfile,
        state: FeatureReasoningState,
    ) -> list[FeatureRecommendation]:
        pass

    @abstractmethod
    def _construct_session(
        self,
        context: FeatureContext,
        state: FeatureReasoningState,
        insights: list[FeatureInsight],
        recommendations: list[FeatureRecommendation],
        proposals: list[FeatureEngineeringProposal],
        ranking_profile: RankingProfile,
    ) -> FeatureSession:
        pass
