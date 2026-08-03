"""
ANOVA Feature Ranking Strategy.

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


class AnovaRankingStrategy(RankingStrategy):
    """
    Computes ANOVA F-value ranking for numerical features against categorical/numerical target.
    """

    @property
    def name(self) -> str:
        return "anova"

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
            from sklearn.feature_selection import f_classif, f_regression

            # Separate numerical features and drop target
            num_cols = [
                c
                for c in context.dataset.numerical_columns
                if c in dataframe.columns and c != target
            ]
            if not num_cols:
                return scores

            # Drop missing values for safety
            df_clean = dataframe[[target] + num_cols].dropna()
            if df_clean.empty:
                return scores

            X = df_clean[num_cols]
            y = df_clean[target]

            problem_type = context.dataset.problem_type or "classification"
            if "regression" in problem_type.lower():
                f_vals, _ = f_regression(X, y)
            else:
                f_vals, _ = f_classif(X, y)

            for col, val in zip(num_cols, f_vals):
                scores[col] = float(val) if pd.notna(val) else 0.0

        except Exception:
            # Fallback to absolute correlation coefficient with target
            for col in context.dataset.numerical_columns:
                if col in dataframe.columns and col != target:
                    try:
                        corr = dataframe[col].corr(dataframe[target])
                        scores[col] = abs(float(corr)) if pd.notna(corr) else 0.0
                    except Exception:
                        scores[col] = 0.0
        return scores
