"""
Mutual Information Feature Ranking Strategy.

Author: Antigravity
License: MIT
"""

import pandas as pd

from mlos.domain.models.feature_intelligence.feature_context import FeatureContext
from mlos.domain.models.feature_intelligence.feature_reasoning_state import (
    FeatureReasoningState,
)
from mlos.feature_intelligence.algorithms.ranking.ranking_strategy import (
    RankingStrategy,
)


class MutualInformationRankingStrategy(RankingStrategy):
    """
    Computes Mutual Information importance scores for numerical and encoded categorical features.
    """

    @property
    def name(self) -> str:
        return "mutual_information"

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
            from sklearn.feature_selection import (
                mutual_info_classif,
                mutual_info_regression,
            )
            from sklearn.preprocessing import LabelEncoder

            all_cols = [
                c
                for c in dataframe.columns
                if c != target
                and c
                in (
                    context.dataset.numerical_columns
                    + context.dataset.categorical_columns
                )
            ]
            if not all_cols:
                return scores

            df_clean = dataframe[[target] + all_cols].dropna()
            if df_clean.empty:
                return scores

            X = pd.DataFrame()
            for col in all_cols:
                if col in context.dataset.categorical_columns:
                    X[col] = LabelEncoder().fit_transform(df_clean[col].astype(str))
                else:
                    X[col] = df_clean[col]

            y = df_clean[target]
            problem_type = context.dataset.problem_type or "classification"

            if "regression" in problem_type.lower():
                mi_vals = mutual_info_regression(X, y)
            else:
                mi_vals = mutual_info_classif(X, y)

            for col, val in zip(all_cols, mi_vals):
                scores[col] = float(val) if pd.notna(val) else 0.0

        except Exception:
            # Fallback to simple correlation absolute values
            for col in dataframe.columns:
                if col != target:
                    try:
                        corr = dataframe[col].corr(dataframe[target])
                        scores[col] = abs(float(corr)) if pd.notna(corr) else 0.0
                    except Exception:
                        scores[col] = 0.0
        return scores
