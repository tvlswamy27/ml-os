from uuid import uuid4

from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_context import (
    LearningContext,
)
from mlos.domain.models.learning.learning_evidence import LearningEvidence
from mlos.domain.models.learning.learning_reasoning_state import (
    ActionStats,
    FeedbackStats,
    LearningReasoningState,
    LearningTrendStats,
)
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.learning.algorithms.learning_algorithm import LearningAlgorithm


class RuleBasedLearningAlgorithm(LearningAlgorithm):
    """
    Concrete LearningAlgorithm implementing statistical heuristics to convert
    Reflection feedback into permanent, proposed optimization updates.
    """

    def can_learn(self, context: LearningContext) -> bool:
        """RuleBasedLearningAlgorithm is always capable of running."""
        return True

    def _analyze_feedback(self, context: LearningContext) -> LearningReasoningState:
        """Processes raw feedback objects into a strongly typed FeedbackStats model."""
        all_reflections = list(context.historical_reflections)
        if context.latest_reflection is not None:
            all_reflections.append(context.latest_reflection)

        total_count = 0
        priority_counts: dict[str, int] = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }
        subsystem_counts: dict[str, int] = {}

        for ref in all_reflections:
            for fb in ref.feedback:
                total_count += 1
                prio = fb.priority.upper() if fb.priority else "MEDIUM"
                priority_counts[prio] = priority_counts.get(prio, 0) + 1
                subsystem_counts[fb.target_subsystem] = (
                    subsystem_counts.get(fb.target_subsystem, 0) + 1
                )

        feedback_stats = FeedbackStats(
            total_feedback_count=total_count,
            priority_counts=priority_counts,
            subsystem_counts=subsystem_counts,
        )

        # Build initial state placeholder
        action_stats = ActionStats(
            action_frequencies={}, repeated_failures=(), repeated_successes=()
        )
        trend_stats = LearningTrendStats(acceptance_history=(), stable_rate=0.0)

        return LearningReasoningState(
            feedback_stats=feedback_stats,
            action_stats=action_stats,
            trend_stats=trend_stats,
        )

    def _group_patterns(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Groups repeated action requests to calculate failure/success rates."""
        all_reflections = list(context.historical_reflections)
        if context.latest_reflection is not None:
            all_reflections.append(context.latest_reflection)

        action_frequencies: dict[str, int] = {}
        failure_components: set[str] = set()
        success_components: set[str] = set()

        for ref in all_reflections:
            for fb in ref.feedback:
                key = f"{fb.action_type}:{fb.target_component}"
                action_frequencies[key] = action_frequencies.get(key, 0) + 1

                # Heuristic grouping of observations based on feedback reasons
                reason_lower = fb.reason.lower()
                if (
                    "fail" in reason_lower
                    or "regress" in reason_lower
                    or "drop" in reason_lower
                ):
                    failure_components.add(fb.target_component)
                elif (
                    "improve" in reason_lower
                    or "success" in reason_lower
                    or "stable" in reason_lower
                ):
                    success_components.add(fb.target_component)

        action_stats = ActionStats(
            action_frequencies=action_frequencies,
            repeated_failures=tuple(sorted(list(failure_components))),
            repeated_successes=tuple(sorted(list(success_components))),
        )

        # Compute trend stats: track acceptance rate history
        acceptance_history = tuple(r.confidence_accepted for r in all_reflections)
        stable_rate = sum(1 for a in acceptance_history if a) / max(
            len(acceptance_history), 1
        )
        trend_stats = LearningTrendStats(
            acceptance_history=acceptance_history, stable_rate=stable_rate
        )

        return LearningReasoningState(
            feedback_stats=state.feedback_stats,
            action_stats=action_stats,
            trend_stats=trend_stats,
        )

    def _rank_learning_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Sorts candidates by priority ('CRITICAL', 'HIGH') and weight support."""
        candidates = []

        # If no active reflection exists, we populate a system initialization proposal
        if context.latest_reflection is None:
            candidates.append(
                {
                    "update_type": LearningUpdateType.REGISTER_PATTERN,
                    "target_subsystem": "system",
                    "target_component": "pipeline",
                    "parameters": {"status": "initialized"},
                    "observations": (
                        "Workspace is initialized with default parameters.",
                    ),
                    "sessions": (),
                }
            )
        else:
            # Analyze active reflection feedback
            latest_ref = context.latest_reflection
            for fb in latest_ref.feedback:
                # Map free-form reflection action_type into structured LearningUpdateType Enum
                raw_action = fb.action_type.upper()
                mapped_type = LearningUpdateType.REGISTER_PATTERN

                if "DISABLE" in raw_action:
                    mapped_type = LearningUpdateType.DISABLE_GENERATOR
                elif "ENABLE" in raw_action:
                    mapped_type = LearningUpdateType.ENABLE_GENERATOR
                elif "ADJUST" in raw_action or "PRIOR" in raw_action:
                    mapped_type = LearningUpdateType.ADJUST_PARAM_PRIOR
                elif "BOOST" in raw_action or "STRENGTHEN" in raw_action:
                    mapped_type = LearningUpdateType.BOOST_HEURISTIC_WEIGHT
                elif "DECREASE" in raw_action or "WEAKEN" in raw_action:
                    mapped_type = LearningUpdateType.DECREASE_HEURISTIC_WEIGHT
                elif "BLACKLIST" in raw_action:
                    mapped_type = LearningUpdateType.BLACKLIST_MODEL
                elif "WHITELIST" in raw_action:
                    mapped_type = LearningUpdateType.WHITELIST_MODEL
                elif "THRESHOLD" in raw_action:
                    mapped_type = LearningUpdateType.UPDATE_THRESHOLD

                candidates.append(
                    {
                        "update_type": mapped_type,
                        "target_subsystem": fb.target_subsystem,
                        "target_component": fb.target_component,
                        "parameters": fb.parameters,
                        "observations": (fb.reason,),
                        "sessions": (latest_ref.session_id,),
                    }
                )

        # Rank candidates: target CRITICAL or HIGH priorities first if present in active feedback
        # Since candidates is a list of dicts, we keep the order
        return LearningReasoningState(
            feedback_stats=state.feedback_stats,
            action_stats=state.action_stats,
            trend_stats=state.trend_stats,
            candidate_updates=tuple(candidates),
        )

    def _validate_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Validates updates to ensure they don't contradict or undo baseline constraints."""
        validated = []
        for cand in state.candidate_updates:
            # Validation rule: We must never disable the core workflow configuration component
            if (
                cand["target_component"] == "core_workflow"
                and cand["update_type"] == LearningUpdateType.DISABLE_GENERATOR
            ):
                continue
            validated.append(cand)

        return LearningReasoningState(
            feedback_stats=state.feedback_stats,
            action_stats=state.action_stats,
            trend_stats=state.trend_stats,
            candidate_updates=tuple(validated),
        )

    def _generate_learning_updates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> tuple[LearningUpdate, ...]:
        """Translates validated candidates to structured, machine-readable LearningUpdate objects."""
        updates = []
        for cand in state.candidate_updates:
            evidence = LearningEvidence(
                reflection_session_ids=cand["sessions"],
                metrics_used=("accuracy",) if context.latest_reflection else (),
                confidence_values=(1.0,) if context.latest_reflection else (),
                frequency_counts=dict(state.action_stats.action_frequencies),
                trend_information={
                    "stable_rate": f"{state.trend_stats.stable_rate:.2f}"
                },
                supporting_observations=cand["observations"],
            )
            upd = LearningUpdate(
                update_id=str(uuid4()),
                update_type=cand["update_type"],
                target_subsystem=cand["target_subsystem"],
                target_component=cand["target_component"],
                parameters=dict(cand["parameters"]),
                evidence=evidence,
            )
            updates.append(upd)
        return tuple(updates)

    def _build_confidence(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningConfidence:
        """Calculates uncertainty and derives the accepted check status."""
        if context.latest_reflection is None:
            # Low history, high uncertainty
            return LearningConfidence(
                score=0.5,
                uncertainty=0.8,
                evidence=(),
                explanation="No reflection history found to validate candidate updates.",
                accepted=False,
            )

        # Baseline confidence matching input reflection stability
        score = 0.85 if context.latest_reflection.confidence_accepted else 0.50
        uncertainty = 0.20 if len(context.historical_reflections) >= 2 else 0.40

        accepted = (score >= 0.70) and (uncertainty <= 0.30)
        return LearningConfidence(
            score=score,
            uncertainty=uncertainty,
            evidence=tuple(
                f"reflection_session:{r.session_id}"
                for r in context.historical_reflections
            ),
            explanation=f"Based on {len(context.historical_reflections) + 1} runs. Heuristic stability stands at {state.trend_stats.stable_rate * 100:.1f}%.",
            accepted=accepted,
        )

    def _construct_session(
        self,
        updates: tuple[LearningUpdate, ...],
        confidence: LearningConfidence,
        state: LearningReasoningState,
    ) -> LearningSession:
        """Assembles variables into the final, frozen LearningSession object."""
        accepted_count = sum(1 for u in updates)
        summary = (
            f"Learning identified {accepted_count} valid pipeline update proposals. "
            f"Confidence: {'ACCEPTED' if confidence.accepted else 'REJECTED'} (score={confidence.score:.2f}, uncertainty={confidence.uncertainty:.2f})."
        )
        return LearningSession(
            summary=summary, updates=list(updates), confidence=confidence
        )
