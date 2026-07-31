"""
HybridReflectionAlgorithm implementation.

Author: Antigravity
License: MIT
"""

from mlos.reflection.algorithms.reflection_algorithm import ReflectionAlgorithm
from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
    RuleBasedReflectionAlgorithm,
)
from mlos.reflection.algorithms.llm_reflection_algorithm import LLMReflectionAlgorithm
from mlos.domain.models.reflection.reflection_context import ReflectionContext
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_reasoning_state import (
    ReflectionReasoningState,
)
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry
from mlos.intelligence.intelligence_service import IntelligenceService


class HybridReflectionAlgorithm(ReflectionAlgorithm):
    """
    Hybrid reflection algorithm coordinating rule-based statistics and LLM analytics
    with validation constraints and graceful fallback.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the hybrid algorithm wrapping rule-based and LLM reflectors.
        """
        self.rule_based_reflector = RuleBasedReflectionAlgorithm()
        self.llm_reflector = LLMReflectionAlgorithm(
            intelligence_service=intelligence_service
        )

    def can_reflect(self, context: ReflectionContext) -> bool:
        """
        Hybrid reflector is always capable of executing.
        """
        return True

    def reflect(self, context: ReflectionContext) -> ReflectionSession:
        """
        Coordinates hybrid reflection flow: runs rule-based analysis, builds LLM inputs,
        validates output, and falls back if necessary.
        """
        # 1. Execute rule-based baseline
        try:
            baseline_session = self.rule_based_reflector.reflect(context)
        except Exception:
            raise

        # 2. Execute LLM reflection
        try:
            llm_session = self.llm_reflector.reflect(context)

            # 3. Validate structured output
            validation_passed = self._validate_session(llm_session, context)

            if validation_passed:
                # Attach telemetry indicating success
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    telemetry = ReflectionTelemetry(
                        provider=tel.provider,
                        model=tel.model,
                        latency_ms=tel.latency_ms,
                        cache_hit=tel.cache_hit,
                        fallback_used=False,
                        validation_passed=True,
                        request_id=tel.request_id,
                        token_usage=tel.token_usage,
                        estimated_cost=tel.estimated_cost,
                    )
                    llm_session = ReflectionSession(
                        summary=llm_session.summary,
                        insights=llm_session.insights,
                        feedback=llm_session.feedback,
                        confidence=llm_session.confidence,
                        telemetry=telemetry,
                    )
                return llm_session
            else:
                # Validation failed, fall back to rule-based session
                fallback_telemetry = None
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    fallback_telemetry = ReflectionTelemetry(
                        provider=tel.provider,
                        model=tel.model,
                        latency_ms=tel.latency_ms,
                        cache_hit=tel.cache_hit,
                        fallback_used=True,
                        validation_passed=False,
                        request_id=tel.request_id,
                        token_usage=tel.token_usage,
                        estimated_cost=tel.estimated_cost,
                    )
                return ReflectionSession(
                    summary=baseline_session.summary,
                    insights=baseline_session.insights,
                    feedback=baseline_session.feedback,
                    confidence=baseline_session.confidence,
                    telemetry=fallback_telemetry,
                )
        except Exception:
            # Provider exception fallback
            provider = "mock"
            model = "mock-gpt"
            service = self.llm_reflector.intelligence_service
            if hasattr(service, "default_config") and service.default_config:
                provider = service.default_config.provider
                model = service.default_config.model
            fallback_telemetry = ReflectionTelemetry(
                provider=provider,
                model=model,
                latency_ms=0.0,
                cache_hit=False,
                fallback_used=True,
                validation_passed=False,
            )
            return ReflectionSession(
                summary=baseline_session.summary,
                insights=baseline_session.insights,
                feedback=baseline_session.feedback,
                confidence=baseline_session.confidence,
                telemetry=fallback_telemetry,
            )

    def _validate_session(
        self, session: ReflectionSession, context: ReflectionContext
    ) -> bool:
        """
        Performs programmatic validation checks to prevent hallucinations and malformed rules.
        """
        conf = session.confidence
        if not conf:
            return False

        # 1. Confidence range check
        if not (0.0 <= conf.score <= 1.0) or not (0.0 <= conf.uncertainty <= 1.0):
            return False

        # 2. Empty insights check (if evaluations history contains runs)
        has_evals = (context.latest_evaluation is not None) or (
            len(context.historical_evaluations) > 0
        )
        if has_evals and len(session.insights) == 0:
            return False

        # 3. Malformed recommendations / priorities / subsystem check
        allowed_priorities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        allowed_subsystems = {
            "planning",
            "decision",
            "generation",
            "assembly",
            "execution",
            "evaluation",
            "reflection",
            "learning",
            "knowledge",
        }

        seen_recommendations = set()

        for fb in session.feedback:
            if fb.priority not in allowed_priorities:
                return False
            if fb.target_subsystem not in allowed_subsystems:
                return False

            # Duplicate recommendations check
            param_key = (
                frozenset(fb.parameters.items()) if fb.parameters else frozenset()
            )
            rec_sig = (
                fb.target_subsystem,
                fb.target_component,
                fb.action_type,
                param_key,
            )
            if rec_sig in seen_recommendations:
                return False
            seen_recommendations.add(rec_sig)

        # 4. Hallucinated metric names check
        valid_metrics: set[str] = set()
        if context.latest_evaluation:
            valid_metrics.update(context.latest_evaluation.metrics.keys())
        for ev in context.historical_evaluations:
            valid_metrics.update(ev.metrics.keys())

        for ins in session.insights:
            # Check for hallucinated metric keys in insight evidence
            for metric in ins.evidence:
                if metric not in valid_metrics:
                    return False

            # 5. Malformed trend check
            if ins.insight_type == "METRIC_TREND":
                direction_found = False
                for d in ["IMPROVING", "DEGRADING", "STABLE"]:
                    if d in ins.summary.upper():
                        direction_found = True
                        break
                if not direction_found:
                    return False

        return True

    def _analyze_history(self, context: ReflectionContext) -> ReflectionReasoningState:
        return self.rule_based_reflector._analyze_history(context)

    def _compare_runs(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> ReflectionReasoningState:
        return self.rule_based_reflector._compare_runs(context, state)

    def _detect_patterns(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> tuple[ReflectionInsight, ...]:
        return ()

    def _generate_recommendations(
        self,
        context: ReflectionContext,
        state: ReflectionReasoningState,
        insights: tuple[ReflectionInsight, ...],
    ) -> tuple[ReflectionFeedback, ...]:
        return ()

    def _construct_session(
        self,
        insights: tuple[ReflectionInsight, ...],
        feedback: tuple[ReflectionFeedback, ...],
        state: ReflectionReasoningState,
    ) -> ReflectionSession:
        return self.rule_based_reflector._construct_session(insights, feedback, state)
