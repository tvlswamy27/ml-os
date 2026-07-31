"""
Reasoning Engine.

Generates recommendations based on project memory.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.recommendation import Recommendation
from mlos.domain.enums.recommendation_priority import RecommendationPriority


class ReasoningEngine:
    """
    Generates ML recommendations.
    """

    def __init__(self):
        """
        Initialize the reasoning engine.
        """

        self.rules = [
            self._apply_duplicate_rule,
            self._apply_missing_value_rule,
            self._apply_categorical_encoding_rule,
        ]

    def reason(
        self,
        memory: ProjectMemory,
    ) -> list[Recommendation]:
        """
        Generate recommendations based on project memory.
        """
        recommendations: list[Recommendation] = []

        if memory.dataset is None:
            return recommendations

        for rule in self.rules:
            rule(
                memory,
                recommendations,
            )

        return recommendations

    def _apply_duplicate_rule(
        self,
        memory: ProjectMemory,
        recommendations: list[Recommendation],
    ) -> None:
        """
        Recommend removing duplicate rows.
        """

        dataset = memory.dataset

        if dataset is None:
            return

        if dataset.duplicate_rows > 0:

            recommendations.append(
                Recommendation(
                    title="Remove Duplicate Rows",
                    description=(
                        f"{dataset.duplicate_rows} duplicate rows detected. "
                        "Consider removing duplicates before training."
                    ),
                    priority=RecommendationPriority.HIGH,
                )
            )

    def _apply_missing_value_rule(
        self,
        memory: ProjectMemory,
        recommendations: list[Recommendation],
    ) -> None:
        """
        Recommend handling missing values.
        """

        dataset = memory.dataset

        if dataset is None:
            return

        missing = {
            column: count
            for column, count in dataset.missing_values.items()
            if count > 0
        }

        if not missing:
            return

        details = "\n".join(
            f"- {column}: {count} missing value(s)" for column, count in missing.items()
        )

        recommendations.append(
            Recommendation(
                title="Handle Missing Values",
                description=(
                    "The following columns contain missing values:\n\n" f"{details}"
                ),
                priority=RecommendationPriority.HIGH,
            )
        )

    def _apply_categorical_encoding_rule(
        self,
        memory: ProjectMemory,
        recommendations: list[Recommendation],
    ) -> None:
        """
        Recommend encoding categorical features.
        """

        dataset = memory.dataset

        if dataset is None:
            return

        if not dataset.categorical_columns:
            return

        columns = "\n".join(f"- {column}" for column in dataset.categorical_columns)

        recommendations.append(
            Recommendation(
                title="Encode Categorical Features",
                description=(
                    "The dataset contains categorical columns:\n\n"
                    f"{columns}\n\n"
                    "These columns should be encoded before model training."
                ),
                priority=RecommendationPriority.MEDIUM,
            )
        )
