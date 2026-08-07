"""
RuleBasedPlanningAlgorithm implementation.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.confidence import Confidence
from mlos.domain.models.planning.evidence import Evidence
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.reasoning_state import ReasoningState
from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm


class RuleBasedPlanningAlgorithm(PlanningAlgorithm):
    """
    Deterministic baseline planning algorithm implementing the 7 protected reasoning phases.
    """

    def can_plan(self, context: PlanningContext) -> bool:
        """
        Always returns True to serve as the baseline rule-based planner.
        """
        return True

    def _analyze_observations(self, context: PlanningContext) -> ReasoningState:
        """
        Inspects observations in the context and returns a type-safe ReasoningState.
        """
        facts = {obs.metric_key: obs.metric_value for obs in context.observations}
        return ReasoningState(facts=facts)

    def _generate_hypotheses(self, reasoning_state: ReasoningState) -> list[Hypothesis]:
        """
        Creates hypotheses about dataset or pipeline improvements based on ReasoningState.
        """
        hypotheses = []

        # Check for missing values fact
        if "missing_values" in reasoning_state.facts:
            hypotheses.append(
                Hypothesis(
                    description="Missing values exist in columns; imputing missing values is required.",
                    target_component="DataImputation",
                    validation_method="CheckMissingValuesAfterImputation",
                )
            )

        # Baseline default hypothesis
        hypotheses.append(
            Hypothesis(
                description="Baseline model should be trained to establish benchmark performance.",
                target_component="ModelTraining",
                validation_method="EvaluateAccuracy",
            )
        )

        return hypotheses

    def _generate_candidate_strategies(
        self, hypotheses: list[Hypothesis]
    ) -> list[CandidateStrategy]:
        """
        Formulates a single CandidateStrategy baseline.
        """
        steps = ["impute", "scale", "train"]
        return [
            CandidateStrategy(
                strategy_name="RuleBasedPipeline",
                description="Baseline preprocessing and model training pipeline",
                steps=steps,
                confidence=None,
            )
        ]

    def _evaluate_candidate_strategies(
        self, candidates: list[CandidateStrategy], hypotheses: list[Hypothesis]
    ) -> dict[str, float]:
        """
        Returns simple baseline score mapping for candidate strategies.
        """
        return {c.strategy_name: 1.0 for c in candidates}

    def _enrich_candidates(
        self,
        candidates: list[CandidateStrategy],
        reasoning_state: ReasoningState,
        hypotheses: list[Hypothesis],
    ) -> list[CandidateStrategy]:
        """
        Enriches candidate strategies with Confidence objects.
        """
        enriched = []
        for c in candidates:
            evidences = []
            for idx, h in enumerate(hypotheses):
                evidences.append(
                    Evidence(
                        source_metric=f"hypothesis_{idx}",
                        result_value=h.description,
                        supports_hypothesis=True,
                    )
                )

            confidence = Confidence(
                confidence_level="HIGH",
                supporting_evidence=evidences,
                uncertainty="LOW",
                assumptions=[],
                explanation="Deterministic baseline strategy generated.",
            )

            enriched.append(
                CandidateStrategy(
                    strategy_name=c.strategy_name,
                    description=c.description,
                    steps=c.steps,
                    confidence=confidence,
                )
            )
        return enriched

    def _select_final_strategy(
        self, candidates: list[CandidateStrategy], scores: dict[str, float]
    ) -> ExecutionStrategy | None:
        """
        Selects the highest scoring candidate and returns its ExecutionStrategy representation.
        """
        if not candidates:
            return None

        # Select the first candidate
        best_candidate = candidates[0]
        return ExecutionStrategy(
            strategy_name=best_candidate.strategy_name,
            topological_steps=best_candidate.steps,
            parameters={"imputer": "mean", "scaler": "standard"},
        )

    def _construct_session(
        self,
        context: PlanningContext,
        hypotheses: list[Hypothesis],
        candidates: list[CandidateStrategy],
        selected: ExecutionStrategy | None,
    ) -> PlanningSession:
        """
        Assembles the final PlanningSession.
        """
        if selected is not None:
            params = dict(selected.parameters)
            steps = list(selected.topological_steps)

            for rule in context.knowledge_summary.rules:
                if (
                    rule.subsystem == "planning"
                    and rule.component == "rule_based_planner"
                ):
                    for k, v in rule.parameters.items():
                        if k == "steps":
                            steps = [s.strip() for s in v.split(",")]
                        else:
                            params[k] = v

            selected = ExecutionStrategy(
                strategy_name=selected.strategy_name,
                topological_steps=steps,
                parameters=params,
            )

        return PlanningSession(
            context=context,
            status="SUCCESS",
            observations=list(context.observations),
            hypotheses=hypotheses,
            candidates=candidates,
            selected_execution_strategy=selected,
        )
