"""
Encoding Strategy.

Generates encoding decisions.

Author: Vikram Tanakala
License: MIT
"""


from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision


class EncodingDecision:

    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:

        decisions: list[Decision] = []
        dataset = memory.dataset

        if dataset is None:
            return decisions

        for column in dataset.categorical_columns:
            unique_count = dataset.unique_values.get(column)

            if unique_count is None:
                continue
            if unique_count <= 10:
                decisions.append(
                    Decision(
                        title=f"Encoding Strategy: {column}",
                        strategy="One-Hot Encoding",
                        confidence="High",
                        reason=f"{column} has only {unique_count} unique values.",
                    )
                )

            else:
                decisions.append(
                    Decision(
                        title=f"Encoding Strategy: {column}",
                        strategy="Label Encoding",
                        confidence="Medium",
                        reason=f"{column} has {unique_count} unique values.",
                    )
                )

        return decisions
