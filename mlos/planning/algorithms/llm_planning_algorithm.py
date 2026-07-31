"""
LLMPlanningAlgorithm implementation.

Author: Vikram Tanakala
License: MIT
"""

from typing import Any
from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.reasoning_state import ReasoningState
from mlos.domain.models.planning.confidence import Confidence
from mlos.domain.models.planning.evidence import Evidence
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.schemas.planning_output import LLMPlanningOutput
from mlos.planning.translator import PlanningTranslator


class LLMPlanningAlgorithm(PlanningAlgorithm):
    """
    LLM-powered planning algorithm executing the Template Method reasoning flow.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the LLM planner, constructing a default intelligence service if none provided.
        """
        if intelligence_service is None:
            import os
            from mlos.planning.config import get_planner_config
            from mlos.intelligence.config import ProviderConfig

            planner_cfg = get_planner_config()
            provider = planner_cfg.get("provider", "mock")
            model = planner_cfg.get("model", "mock-gpt")
            temperature = float(planner_cfg.get("temperature", 0.0))

            config = ProviderConfig(
                provider=provider,
                model=model,
                temperature=temperature,
                api_key=os.environ.get("OPENAI_API_KEY"),
            )
            intelligence_service = IntelligenceService(default_config=config)

        self.intelligence_service = intelligence_service
        self._last_parsed_output: LLMPlanningOutput | None = None
        self._last_telemetry: Any = None

    def can_plan(self, context: PlanningContext) -> bool:
        """
        LLM planner can plan for any context.
        """
        return True

    def plan(self, context: PlanningContext) -> PlanningSession:
        """
        Executes the LLM request, stores parsed outputs and telemetry,
        then invokes super().plan() to run the 7 template method phases.
        """
        # Execute subsystem prompt through the Intelligence layer
        response = self.intelligence_service.execute_subsystem(
            "planning", context, LLMPlanningOutput
        )

        if not response.validation_passed or response.parsed_output is None:
            raise ValueError(f"LLM Planning generation failed: {response.raw_response}")

        self._last_parsed_output = response.parsed_output

        # Construct typed telemetry object
        from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry

        token_usage = {}
        if response.call_metrics and response.call_metrics.token_usage:
            tu = response.call_metrics.token_usage
            token_usage = {
                "input_tokens": tu.input_tokens,
                "output_tokens": tu.output_tokens,
                "total_tokens": tu.total_tokens,
            }

        self._last_telemetry = PlanningTelemetry(
            provider=response.provider,
            model=response.model,
            latency_ms=response.latency,
            cache_hit=response.cache_hit,
            fallback_used=False,
            validation_passed=response.validation_passed,
            request_id=(
                response.call_metrics.request_id if response.call_metrics else ""
            ),
            token_usage=token_usage,
            estimated_cost=response.cost,
        )

        # Run template method flow
        return super().plan(context)

    def _analyze_observations(self, context: PlanningContext) -> ReasoningState:
        """
        Extract reasoning fact from the parsed output.
        """
        reasoning = (
            self._last_parsed_output.reasoning if self._last_parsed_output else ""
        )
        return ReasoningState(facts={"reasoning": reasoning})

    def _generate_hypotheses(self, reasoning_state: ReasoningState) -> list[Hypothesis]:
        """
        Create hypotheses from selected and alternative candidate strategies.
        """
        if not self._last_parsed_output:
            return []

        hypotheses = []
        main_evidence = Evidence(
            source_metric="llm_reasoning",
            result_value=self._last_parsed_output.reasoning,
            supports_hypothesis=True,
        )
        hypotheses.append(
            Hypothesis(
                description=self._last_parsed_output.reasoning,
                target_component=self._last_parsed_output.strategy_name,
                validation_method="EvaluatePerformance",
                evidences=[main_evidence],
            )
        )

        for alt in self._last_parsed_output.alternative_candidates:
            hypotheses.append(
                Hypothesis(
                    description=f"Alternative candidate strategy: {alt.strategy_name} - {alt.description}",
                    target_component=alt.strategy_name,
                    validation_method="ComparePerformance",
                    evidences=[],
                )
            )

        return hypotheses

    def _generate_candidate_strategies(
        self, hypotheses: list[Hypothesis]
    ) -> list[CandidateStrategy]:
        """
        Build CandidateStrategy objects.
        """
        if not self._last_parsed_output:
            return []

        main_cand = CandidateStrategy(
            strategy_name=self._last_parsed_output.strategy_name,
            description=self._last_parsed_output.strategy_description,
            steps=self._last_parsed_output.topological_steps,
            confidence=None,
        )
        candidates = [main_cand]

        for alt in self._last_parsed_output.alternative_candidates:
            candidates.append(
                CandidateStrategy(
                    strategy_name=alt.strategy_name,
                    description=alt.description,
                    steps=alt.steps,
                    confidence=None,
                )
            )

        return candidates

    def _evaluate_candidate_strategies(
        self, candidates: list[CandidateStrategy], hypotheses: list[Hypothesis]
    ) -> dict[str, float]:
        """
        Score candidate strategies using output confidence.
        """
        scores = {}
        if candidates and self._last_parsed_output:
            scores[candidates[0].strategy_name] = self._last_parsed_output.confidence
            for alt in candidates[1:]:
                scores[alt.strategy_name] = 0.5
        return scores

    def _enrich_candidates(
        self,
        candidates: list[CandidateStrategy],
        reasoning_state: ReasoningState,
        hypotheses: list[Hypothesis],
    ) -> list[CandidateStrategy]:
        """
        Enrich candidate strategies with Confidence objects.
        """
        if not candidates or not self._last_parsed_output:
            return []

        conf_val = self._last_parsed_output.confidence
        conf_level = (
            "HIGH" if conf_val >= 0.8 else ("MEDIUM" if conf_val >= 0.5 else "LOW")
        )

        main_evidence = Evidence(
            source_metric="llm_reasoning",
            result_value=self._last_parsed_output.reasoning,
            supports_hypothesis=True,
        )
        main_confidence = Confidence(
            confidence_level=conf_level,
            supporting_evidence=[main_evidence],
            uncertainty="LOW" if conf_level == "HIGH" else "MEDIUM",
            explanation=self._last_parsed_output.reasoning,
        )

        enriched = [
            CandidateStrategy(
                strategy_name=candidates[0].strategy_name,
                description=candidates[0].description,
                steps=candidates[0].steps,
                confidence=main_confidence,
            )
        ]

        for alt in candidates[1:]:
            alt_confidence = Confidence(
                confidence_level="MEDIUM",
                supporting_evidence=[],
                uncertainty="MEDIUM",
                explanation=alt.description,
            )
            enriched.append(
                CandidateStrategy(
                    strategy_name=alt.strategy_name,
                    description=alt.description,
                    steps=alt.steps,
                    confidence=alt_confidence,
                )
            )

        return enriched

    def _select_final_strategy(
        self, candidates: list[CandidateStrategy], scores: dict[str, float]
    ) -> ExecutionStrategy | None:
        """
        Formulate selected ExecutionStrategy.
        """
        if not candidates or not self._last_parsed_output:
            return None
        return ExecutionStrategy(
            strategy_name=self._last_parsed_output.strategy_name,
            topological_steps=self._last_parsed_output.topological_steps,
            parameters=self._last_parsed_output.parameters,
        )

    def _construct_session(
        self,
        context: PlanningContext,
        hypotheses: list[Hypothesis],
        candidates: list[CandidateStrategy],
        selected: ExecutionStrategy | None,
    ) -> PlanningSession:
        """
        Assemble final session via PlanningTranslator.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            raise ValueError("No LLM planning output or telemetry cached.")

        return PlanningTranslator.to_planning_session(
            context=context,
            output=self._last_parsed_output,
            telemetry=self._last_telemetry,
        )
