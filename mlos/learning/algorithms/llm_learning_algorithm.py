"""
LLMLearningAlgorithm implementation.

Author: Antigravity
License: MIT
"""

import os
from typing import Any
from mlos.learning.algorithms.learning_algorithm import LearningAlgorithm
from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_reasoning_state import (
    LearningReasoningState,
)
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.schemas.learning_output import LLMLearningOutput
from mlos.learning.translator import LearningTranslator


class LLMLearningAlgorithm(LearningAlgorithm):
    """
    LLM-powered learning algorithm executing the Template Method reasoning flow.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the LLM learner, constructing a default intelligence service if none provided.
        """
        if intelligence_service is None:
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
        self._last_parsed_output: LLMLearningOutput | None = None
        self._last_telemetry: LearningTelemetry | None = None
        self._current_context: LearningContext | None = None

    def can_learn(self, context: LearningContext) -> bool:
        """
        LLM learner is capable of learning over any context.
        """
        return True

    def learn(self, context: LearningContext) -> LearningSession:
        """
        Executes the LLM request, stores parsed outputs and telemetry,
        then invokes super().learn() to run the template method phases.
        """
        self._current_context = context

        response = self.intelligence_service.execute_subsystem(
            "learning", context, LLMLearningOutput
        )

        if not response.validation_passed or response.parsed_output is None:
            raise ValueError(f"LLM Learning generation failed: {response.raw_response}")

        self._last_parsed_output = response.parsed_output

        token_usage = {}
        if response.call_metrics and response.call_metrics.token_usage:
            tu = response.call_metrics.token_usage
            token_usage = {
                "input_tokens": tu.input_tokens,
                "output_tokens": tu.output_tokens,
                "total_tokens": tu.total_tokens,
            }

        self._last_telemetry = LearningTelemetry(
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
        return super().learn(context)

    def _analyze_feedback(self, context: LearningContext) -> LearningReasoningState:
        """
        Step 1: Programmatic feedback analysis (shares RuleBased logic).
        """
        from mlos.learning.algorithms.rule_based_learning_algorithm import (
            RuleBasedLearningAlgorithm,
        )

        rule_based = RuleBasedLearningAlgorithm()
        return rule_based._analyze_feedback(context)

    def _group_patterns(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """
        Step 2: Programmatic pattern grouping (shares RuleBased logic).
        """
        from mlos.learning.algorithms.rule_based_learning_algorithm import (
            RuleBasedLearningAlgorithm,
        )

        rule_based = RuleBasedLearningAlgorithm()
        return rule_based._group_patterns(context, state)

    def _rank_learning_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """
        Step 3: Programmatic candidate ranking (shares RuleBased logic).
        """
        from mlos.learning.algorithms.rule_based_learning_algorithm import (
            RuleBasedLearningAlgorithm,
        )

        rule_based = RuleBasedLearningAlgorithm()
        return rule_based._rank_learning_candidates(context, state)

    def _validate_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """
        Step 4: Programmatic validation candidates checks (shares RuleBased logic).
        """
        from mlos.learning.algorithms.rule_based_learning_algorithm import (
            RuleBasedLearningAlgorithm,
        )

        rule_based = RuleBasedLearningAlgorithm()
        return rule_based._validate_candidates(context, state)

    def _generate_learning_updates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> tuple[LearningUpdate, ...]:
        """
        Step 5: Exposes updates parsed from the LLM output.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            return ()
        session = LearningTranslator.to_learning_session(
            context, self._last_parsed_output, self._last_telemetry
        )
        return tuple(session.updates)

    def _build_confidence(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningConfidence:
        """
        Step 6: Exposes confidence parsed from the LLM output.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            return LearningConfidence(score=0.0, uncertainty=1.0)
        session = LearningTranslator.to_learning_session(
            context, self._last_parsed_output, self._last_telemetry
        )
        if session.confidence is None:
            return LearningConfidence(score=0.0, uncertainty=1.0)
        return session.confidence

    def _construct_session(
        self,
        updates: tuple[LearningUpdate, ...],
        confidence: LearningConfidence,
        state: LearningReasoningState,
    ) -> LearningSession:
        """
        Step 7: Assemble final session via translator.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            raise ValueError("No LLM learning output or telemetry cached.")

        context = self._current_context
        if context is None:
            context = LearningContext(
                project_name="unknown",
                project_goal="unknown",
                latest_reflection=None,
            )

        return LearningTranslator.to_learning_session(
            context=context,
            output=self._last_parsed_output,
            telemetry=self._last_telemetry,
        )
