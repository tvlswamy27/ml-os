"""
Permutation Importance Feature Ranking Strategy.

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


class PermutationImportanceRankingStrategy(RankingStrategy):
    """
    Computes Permutation Importance scores.
    """

    @property
    def name(self) -> str:
        return "permutation_importance"

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
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.inspection import permutation_importance
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

            df_clean = dataframe[[target] + all_cols].copy()
            for col in all_cols:
                if col in context.dataset.categorical_columns:
                    df_clean[col] = LabelEncoder().fit_transform(
                        df_clean[col].astype(str)
                    )
                else:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())

            df_clean[target] = (
                df_clean[target].fillna(method="ffill").fillna(method="bfill")
            )

            X = df_clean[all_cols]
            y = df_clean[target]

            problem_type = context.dataset.problem_type or "classification"
            if "regression" in problem_type.lower():
                model = RandomForestRegressor(n_estimators=30, random_state=42)
                model.fit(X, y)
                result = permutation_importance(
                    model, X, y, n_repeats=5, random_state=42
                )
            else:
                y_encoded = LabelEncoder().fit_transform(y.astype(str))
                model = RandomForestClassifier(n_estimators=30, random_state=42)
                model.fit(X, y_encoded)
                result = permutation_importance(
                    model, X, y_encoded, n_repeats=5, random_state=42
                )

            for col, val in zip(all_cols, result.importances_mean):
                scores[col] = float(val) if pd.notna(val) else 0.0

        except Exception:
            # Fallback to absolute correlation coefficient with target
            for col in dataframe.columns:
                if col != target:
                    try:
                        corr = dataframe[col].corr(dataframe[target])
                        scores[col] = abs(float(corr)) if pd.notna(corr) else 0.0
                    except Exception:
                        scores[col] = 0.0
        return scores
