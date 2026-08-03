"""
Chi-Square Feature Ranking Strategy.

Author: Antigravity
License: MIT
"""

import pandas as pd
from mlos.feature_intelligence.algorithms.ranking.ranking_strategy import (
    RankingStrategy,
)
from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)


class ChiSquareRankingStrategy(RankingStrategy):
    """
    Computes Chi-Square statistics for categorical features against categorical target.
    """

    @property
    def name(self) -> str:
        return "chi_square"

    def score_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        if context.dataset is None or context.dataset.target is None:
            return scores

        target = context.dataset.target
        if target not in dataframe.columns:
            return scores

        try:
            from sklearn.feature_selection import chi2
            from sklearn.preprocessing import LabelEncoder

            cat_cols = [
                c
                for c in context.dataset.categorical_columns
                if c in dataframe.columns and c != target
            ]
            if not cat_cols:
                return scores

            df_clean = dataframe[[target] + cat_cols].dropna()
            if df_clean.empty:
                return scores

            # Encode categories to integers
            X_encoded = pd.DataFrame()
            for col in cat_cols:
                X_encoded[col] = LabelEncoder().fit_transform(df_clean[col].astype(str))

            y_encoded = LabelEncoder().fit_transform(df_clean[target].astype(str))

            chi_scores, _ = chi2(X_encoded, y_encoded)
            for col, val in zip(cat_cols, chi_scores):
                scores[col] = float(val) if pd.notna(val) else 0.0

        except Exception:
            # Fallback based on unique value ratio
            for col in context.dataset.categorical_columns:
                if col in dataframe.columns and col != target:
                    try:
                        scores[col] = float(dataframe[col].nunique())
                    except Exception:
                        scores[col] = 0.0
        return scores
