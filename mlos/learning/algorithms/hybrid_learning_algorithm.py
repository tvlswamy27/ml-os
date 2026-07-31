"""
HybridLearningAlgorithm implementation.

Author: Antigravity
License: MIT
"""

from mlos.learning.algorithms.learning_algorithm import LearningAlgorithm
from mlos.learning.algorithms.rule_based_learning_algorithm import (
    RuleBasedLearningAlgorithm,
)
from mlos.learning.algorithms.llm_learning_algorithm import LLMLearningAlgorithm
from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_reasoning_state import (
    LearningReasoningState,
)
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.intelligence.intelligence_service import IntelligenceService


class HybridLearningAlgorithm(LearningAlgorithm):
    """
    Hybrid learning algorithm coordinating rule-based statistics and LLM proposals
    with validation checks and fallback.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the hybrid algorithm wrapping rule-based and LLM learners.
        """
        self.rule_based_learner = RuleBasedLearningAlgorithm()
        self.llm_learner = LLMLearningAlgorithm(
            intelligence_service=intelligence_service
        )

    def can_learn(self, context: LearningContext) -> bool:
        """
        Hybrid learner is always capable of executing.
        """
        return True

    def learn(self, context: LearningContext) -> LearningSession:
        """
        Coordinates hybrid learning flow.
        """
        # 1. Execute rule-based baseline
        try:
            baseline_session = self.rule_based_learner.learn(context)
        except Exception:
            raise

        # 2. Execute LLM learning
        try:
            llm_session = self.llm_reflector_reflect(context)

            # 3. Validate structured output
            validation_passed = self._validate_session(llm_session, context)

            if validation_passed:
                # Attach telemetry indicating success
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    telemetry = LearningTelemetry(
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
                    llm_session = LearningSession(
                        summary=llm_session.summary,
                        updates=llm_session.updates,
                        confidence=llm_session.confidence,
                        telemetry=telemetry,
                    )
                return llm_session
            else:
                # Validation failed, fall back to rule-based baseline
                fallback_telemetry = None
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    fallback_telemetry = LearningTelemetry(
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
                return LearningSession(
                    summary=baseline_session.summary,
                    updates=baseline_session.updates,
                    confidence=baseline_session.confidence,
                    telemetry=fallback_telemetry,
                )
        except Exception:
            # Provider exception fallback
            provider = "mock"
            model = "mock-gpt"
            service = self.llm_learner.intelligence_service
            if hasattr(service, "default_config") and service.default_config:
                provider = service.default_config.provider
                model = service.default_config.model
            fallback_telemetry = LearningTelemetry(
                provider=provider,
                model=model,
                latency_ms=0.0,
                cache_hit=False,
                fallback_used=True,
                validation_passed=False,
            )
            return LearningSession(
                summary=baseline_session.summary,
                updates=baseline_session.updates,
                confidence=baseline_session.confidence,
                telemetry=fallback_telemetry,
            )

    def llm_reflector_reflect(self, context: LearningContext) -> LearningSession:
        return self.llm_learner.learn(context)

    def _validate_session(
        self, session: LearningSession, context: LearningContext
    ) -> bool:
        """
        Performs programmatic validation checks on LLM proposed updates.
        """
        conf = session.confidence
        if not conf:
            return False

        # 1. Confidence range check
        if not (0.0 <= conf.score <= 1.0) or not (0.0 <= conf.uncertainty <= 1.0):
            return False

        # 2. Empty proposals check (if reflections history exists)
        has_reflections = (context.latest_reflection is not None) or (
            len(context.historical_reflections) > 0
        )
        if has_reflections and len(session.updates) == 0:
            return False

        parsed = self.llm_learner._last_parsed_output
        if not parsed:
            return False

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

        # Collect valid components and active knowledge keys
        valid_components = set()
        all_reflections = list(context.historical_reflections)
        if context.latest_reflection:
            all_reflections.append(context.latest_reflection)
        for r in all_reflections:
            for fb in r.feedback:
                valid_components.add(fb.target_component)

        active_sigs = set()
        for rule in getattr(context.knowledge_summary, "rules", []):
            param_key = (
                frozenset(rule.parameters.items()) if rule.parameters else frozenset()
            )
            active_sigs.add((rule.subsystem, rule.component, param_key))

        seen_proposals = set()

        for prop in parsed.proposals:
            # 3. Update types check
            try:
                LearningUpdateType(prop.update_type)
            except ValueError:
                return False

            # 4. Priorities & subsystems check
            if prop.priority not in allowed_priorities:
                return False
            if prop.target_subsystem not in allowed_subsystems:
                return False

            # 5. Duplicated proposals check
            param_key = (
                frozenset(prop.parameters.items()) if prop.parameters else frozenset()
            )
            sig = (
                prop.target_subsystem,
                prop.target_component,
                prop.update_type,
                param_key,
            )
            if sig in seen_proposals:
                return False
            seen_proposals.add(sig)

            # 6. Hallucinated actions check
            if valid_components and prop.target_component not in valid_components:
                return False

            # 7. Malformed evidence check
            ev = prop.evidence
            if (
                not ev.reflection_session_ids
                and not ev.evaluation_session_ids
                and not ev.execution_session_ids
            ):
                return False

            # 8. Proposals already represented by ACTIVE Knowledge check
            if (
                prop.target_subsystem,
                prop.target_component,
                param_key,
            ) in active_sigs:
                return False

        return True

    def _analyze_feedback(self, context: LearningContext) -> LearningReasoningState:
        return self.rule_based_learner._analyze_feedback(context)

    def _group_patterns(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        return self.rule_based_learner._group_patterns(context, state)

    def _rank_learning_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        return self.rule_based_learner._rank_learning_candidates(context, state)

    def _validate_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        return self.rule_based_learner._validate_candidates(context, state)

    def _generate_learning_updates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> tuple[LearningUpdate, ...]:
        return ()

    def _build_confidence(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningConfidence:
        return self.rule_based_learner._build_confidence(context, state)

    def _construct_session(
        self,
        updates: tuple[LearningUpdate, ...],
        confidence: LearningConfidence,
        state: LearningReasoningState,
    ) -> LearningSession:
        return self.rule_based_learner._construct_session(updates, confidence, state)
