from mlos.decision.strategies.base_strategy import BaseStrategy
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision

from mlos.knowledge.preprocessing import (
    DROP_COLUMN,
    MEDIAN_IMPUTATION,
    MODE_IMPUTATION,
)

from mlos.knowledge.thresholds import (
    HIGH_MISSING_THRESHOLD,
)

class MissingValueDecision(BaseStrategy):

    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:
        """
        Decide how to handle missing values.
        """

        decisions = []

        dataset = memory.dataset

        if dataset is None:
            return decisions

        for column, missing_count in dataset.missing_values.items():

            if missing_count == 0:
                continue

            missing_percentage = dataset.missing_percentages[column]

            column_type = dataset.column_types[column]

            if missing_percentage > HIGH_MISSING_THRESHOLD:

                strategy = DROP_COLUMN

                confidence = "High"

                reason = (
                    f"{column} has "
                    f"{missing_percentage}% missing values."
                )

            elif column_type == "numerical":

                strategy = MEDIAN_IMPUTATION

                confidence = "High"

                reason = (
                    f"{column} is numerical with "
                    f"{missing_percentage}% missing values."
                )

            else:

                strategy = MODE_IMPUTATION

                confidence = "High"

                reason = (
                    f"{column} is categorical with "
                    f"{missing_percentage}% missing values."
                )

            decisions.append(

                Decision(

                    title=f"Missing Value Strategy: {column}",

                    strategy=strategy,

                    confidence=confidence,

                    reason=reason,

                )

            )

        return decisions
