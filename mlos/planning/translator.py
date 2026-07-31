"""
PlanningTranslator implementation.

Responsible for translating LLM planning outputs into domain models.

Author: Vikram Tanakala
License: MIT
"""

from mlos.intelligence.schemas.planning_output import LLMPlanningOutput
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.confidence import Confidence
from mlos.domain.models.planning.evidence import Evidence
from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry


class PlanningTranslator:
    """
    Translator that converts LLM structured output to ML-OS planning domain models.
    """

    @staticmethod
    def to_planning_session(
        context: PlanningContext,
        output: LLMPlanningOutput,
        telemetry: PlanningTelemetry,
    ) -> PlanningSession:
        """
        Convert structured LLMPlanningOutput to PlanningSession.
        """
        # Determine confidence level
        conf_val = output.confidence
        if conf_val >= 0.8:
            conf_level = "HIGH"
        elif conf_val >= 0.5:
            conf_level = "MEDIUM"
        else:
            conf_level = "LOW"

        main_evidence = Evidence(
            source_metric="llm_reasoning",
            result_value=output.reasoning,
            supports_hypothesis=True,
        )

        main_confidence = Confidence(
            confidence_level=conf_level,
            supporting_evidence=[main_evidence],
            uncertainty="LOW" if conf_level == "HIGH" else "MEDIUM",
            assumptions=[],
            explanation=output.reasoning,
        )

        # Main strategy candidate
        main_candidate = CandidateStrategy(
            strategy_name=output.strategy_name,
            description=output.strategy_description,
            steps=output.topological_steps,
            confidence=main_confidence,
        )

        candidates = [main_candidate]

        # Alternative candidate strategies
        for alt in output.alternative_candidates:
            alt_evidence = Evidence(
                source_metric="llm_alternative",
                result_value=alt.description,
                supports_hypothesis=True,
            )
            alt_confidence = Confidence(
                confidence_level="MEDIUM",
                supporting_evidence=[alt_evidence],
                uncertainty="MEDIUM",
                assumptions=[],
                explanation=alt.description,
            )
            candidates.append(
                CandidateStrategy(
                    strategy_name=alt.strategy_name,
                    description=alt.description,
                    steps=alt.steps,
                    confidence=alt_confidence,
                )
            )

        # Build Hypotheses
        hypotheses = []
        # Selected strategy hypothesis
        hypotheses.append(
            Hypothesis(
                description=output.reasoning,
                target_component=output.strategy_name,
                validation_method="EvaluatePerformance",
                evidences=[main_evidence],
            )
        )
        # Alternative strategy hypotheses
        for alt in output.alternative_candidates:
            hypotheses.append(
                Hypothesis(
                    description=f"Alternative candidate strategy: {alt.strategy_name} - {alt.description}",
                    target_component=alt.strategy_name,
                    validation_method="ComparePerformance",
                    evidences=[],
                )
            )

        # Build Execution Strategy
        selected_strategy = ExecutionStrategy(
            strategy_name=output.strategy_name,
            topological_steps=output.topological_steps,
            parameters=output.parameters,
        )

        return PlanningSession(
            context=context,
            status="SUCCESS",
            observations=list(context.observations),
            hypotheses=hypotheses,
            candidates=candidates,
            selected_execution_strategy=selected_strategy,
            telemetry=telemetry,
        )
