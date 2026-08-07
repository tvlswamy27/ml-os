"""
LLMReflectionAlgorithm implementation.

Author: Antigravity
License: MIT
"""

import os

from mlos.domain.models.reflection.reflection_context import ReflectionContext
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_reasoning_state import (
    ReflectionReasoningState,
)
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.schemas.reflection_output import LLMReflectionOutput
from mlos.reflection.algorithms.reflection_algorithm import ReflectionAlgorithm
from mlos.reflection.translator import ReflectionTranslator


class LLMReflectionAlgorithm(ReflectionAlgorithm):
    """
    LLM-powered reflection algorithm executing the Template Method reasoning flow.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the LLM reflector, constructing a default intelligence service if none provided.
        """
        if intelligence_service is None:
            from mlos.intelligence.config import ProviderConfig
            from mlos.planning.config import get_planner_config

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
        self._last_parsed_output: LLMReflectionOutput | None = None
        self._last_telemetry: ReflectionTelemetry | None = None
        self._current_context: ReflectionContext | None = None

    def can_reflect(self, context: ReflectionContext) -> bool:
        """
        LLM reflector is capable of reflecting over any context.
        """
        return True

    def reflect(self, context: ReflectionContext) -> ReflectionSession:
        """
        Executes the LLM request, stores parsed outputs and telemetry,
        then invokes super().reflect() to run the template method phases.
        """
        self._current_context = context

        response = self.intelligence_service.execute_subsystem(
            "reflection", context, LLMReflectionOutput
        )

        if not response.validation_passed or response.parsed_output is None:
            raise ValueError(
                f"LLM Reflection generation failed: {response.raw_response}"
            )

        self._last_parsed_output = response.parsed_output

        token_usage = {}
        if response.call_metrics and response.call_metrics.token_usage:
            tu = response.call_metrics.token_usage
            token_usage = {
                "input_tokens": tu.input_tokens,
                "output_tokens": tu.output_tokens,
                "total_tokens": tu.total_tokens,
            }

        self._last_telemetry = ReflectionTelemetry(
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
        return super().reflect(context)

    def _analyze_history(self, context: ReflectionContext) -> ReflectionReasoningState:
        """
        Step 1: Programmatic history analysis (shares RuleBased logic).
        """
        from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
            RuleBasedReflectionAlgorithm,
        )

        rule_based = RuleBasedReflectionAlgorithm()
        return rule_based._analyze_history(context)

    def _compare_runs(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> ReflectionReasoningState:
        """
        Step 2: Programmatic pairwise comparisons (shares RuleBased logic).
        """
        from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
            RuleBasedReflectionAlgorithm,
        )

        rule_based = RuleBasedReflectionAlgorithm()
        return rule_based._compare_runs(context, state)

    def _detect_patterns(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> tuple[ReflectionInsight, ...]:
        """
        Step 3: Exposes insights parsed from the LLM output.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            return ()
        session = ReflectionTranslator.to_reflection_session(
            context, self._last_parsed_output, self._last_telemetry
        )
        return tuple(session.insights)

    def _generate_recommendations(
        self,
        context: ReflectionContext,
        state: ReflectionReasoningState,
        insights: tuple[ReflectionInsight, ...],
    ) -> tuple[ReflectionFeedback, ...]:
        """
        Step 4: Exposes feedback recommendations parsed from the LLM output.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            return ()
        session = ReflectionTranslator.to_reflection_session(
            context, self._last_parsed_output, self._last_telemetry
        )
        return tuple(session.feedback)

    def _construct_session(
        self,
        insights: tuple[ReflectionInsight, ...],
        feedback: tuple[ReflectionFeedback, ...],
        state: ReflectionReasoningState,
    ) -> ReflectionSession:
        """
        Step 5: Assemble insights and feedback into a final ReflectionSession.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            raise ValueError("No LLM reflection output or telemetry cached.")

        context = self._current_context
        if context is None:
            context = ReflectionContext(
                project_name="unknown",
                project_goal="unknown",
                latest_planning=None,
                latest_execution=None,
                latest_evaluation=None,
            )

        return ReflectionTranslator.to_reflection_session(
            context=context,
            output=self._last_parsed_output,
            telemetry=self._last_telemetry,
        )
