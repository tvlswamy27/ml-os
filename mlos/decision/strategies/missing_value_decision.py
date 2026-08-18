from mlos.decision.strategies.base_strategy import BaseStrategy
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
        context,
    ) -> list[Decision]:
        """
        Decide how to handle missing values.
        """
        from mlos.domain.models.decision_context import DecisionContext

        if isinstance(context, DecisionContext):
            memory = context.project_memory
        else:
            memory = context

        decisions: list[Decision] = []

        dataset = memory.dataset

        if dataset is None:
            return decisions

        active_rule = self.get_active_rule(context, "missing_value")

        for column, missing_count in dataset.missing_values.items():

            if missing_count == 0:
                continue

            strategy = None
            confidence = "High"
            reason = ""
            if active_rule:
                strategy = active_rule.parameters.get(
                    column
                ) or active_rule.parameters.get("strategy")
                if strategy:
                    reason = f"Overridden by active knowledge rule (version {active_rule.version_number})."
                    confidence = f"{active_rule.confidence_score * 100:.0f}%"

            if not strategy:
                missing_percentage = dataset.missing_percentages[column]
                column_type = dataset.column_types[column]

                if missing_percentage > HIGH_MISSING_THRESHOLD:
                    strategy = DROP_COLUMN
                    confidence = "High"
                    reason = f"{column} has {missing_percentage}% missing values."
                elif column_type == "numerical":
                    strategy = MEDIAN_IMPUTATION
                    confidence = "High"
                    reason = f"{column} is numerical with {missing_percentage}% missing values."
                else:
                    strategy = MODE_IMPUTATION
                    confidence = "High"
                    reason = f"{column} is categorical with {missing_percentage}% missing values."

            decisions.append(
                Decision(
                    title=f"Missing Value Strategy: {column}",
                    strategy=strategy,
                    confidence=confidence,
                    reason=reason,
                    columns=[column],
                )
            )

        return decisions
