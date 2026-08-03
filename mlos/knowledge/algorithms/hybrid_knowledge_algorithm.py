"""
HybridKnowledgeAlgorithm implementation.

Author: Antigravity
License: MIT
"""

from mlos.knowledge.algorithms.knowledge_algorithm import KnowledgeAlgorithm
from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
    RuleBasedKnowledgeAlgorithm,
)
from mlos.knowledge.algorithms.llm_knowledge_algorithm import (
    LLMKnowledgeAlgorithm,
)
from mlos.domain.models.knowledge.knowledge_context import KnowledgeContext
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_reasoning_state import (
    KnowledgeReasoningState,
)
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_promotion_decision import (
    KnowledgePromotionType,
    KnowledgePromotionDecision,
)
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry
from mlos.intelligence.intelligence_service import IntelligenceService


class HybridKnowledgeAlgorithm(KnowledgeAlgorithm):
    """
    Hybrid knowledge management algorithm coordinating baseline analysis,
    LLM promotions, safety validation constraints, and fallback.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the hybrid coordinator.
        """
        self.rule_based_learner = RuleBasedKnowledgeAlgorithm()
        self.llm_learner = LLMKnowledgeAlgorithm(
            intelligence_service=intelligence_service
        )

    def can_manage(self, context: KnowledgeContext) -> bool:
        """
        Hybrid learner is always capable of running.
        """
        return True

    def manage(self, context: KnowledgeContext) -> KnowledgeSession:
        """
        Executes hybrid execution pipeline.
        """
        # 1. Execute rule-based baseline
        try:
            baseline_session = self.rule_based_learner.manage(context)
        except Exception:
            raise

        # 2. Run LLM knowledge management
        try:
            llm_session = self.llm_learner.manage(context)

            # 3. Validate structured promotions and transitions
            validation_passed = self._validate_session(llm_session, context)

            if validation_passed:
                # Add successful telemetry
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    telemetry = KnowledgeTelemetry(
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
                    llm_session = KnowledgeSession(
                        summary=llm_session.summary,
                        promoted_entries=llm_session.promoted_entries,
                        conflicts=llm_session.conflicts,
                        telemetry=telemetry,
                    )
                return llm_session
            else:
                # Validation failed, fall back
                fallback_telemetry = None
                if llm_session.telemetry:
                    tel = llm_session.telemetry
                    fallback_telemetry = KnowledgeTelemetry(
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
                return KnowledgeSession(
                    summary=baseline_session.summary,
                    promoted_entries=baseline_session.promoted_entries,
                    conflicts=baseline_session.conflicts,
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
            fallback_telemetry = KnowledgeTelemetry(
                provider=provider,
                model=model,
                latency_ms=0.0,
                cache_hit=False,
                fallback_used=True,
                validation_passed=False,
            )
            return KnowledgeSession(
                summary=baseline_session.summary,
                promoted_entries=baseline_session.promoted_entries,
                conflicts=baseline_session.conflicts,
                telemetry=fallback_telemetry,
            )

    def _validate_session(
        self, session: KnowledgeSession, context: KnowledgeContext
    ) -> bool:
        """
        Verifies LLM promotion decisions against safety, version, and lineage rules.
        """
        parsed = self.llm_learner._last_parsed_output
        if not parsed:
            return False

        # 1. Empty check (if accepted learning exists)
        has_learning = (context.latest_learning is not None) and (
            context.latest_learning.confidence_accepted
        )
        if has_learning and not parsed.promotions:
            return False

        # Build indexes
        active_entries = {}
        if context.existing_knowledge is not None:
            for e in context.existing_knowledge.active_entries:
                active_entries[e.knowledge_id] = e

        incoming_updates = {}
        if context.latest_learning is not None:
            for u in context.latest_learning.updates:
                incoming_updates[u.update_id] = u

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

        seen_promotions = set()
        seen_decision_ids = set()
        seen_conflicts = set()

        for dec in parsed.promotions:
            # 2. Status transition checks
            try:
                dtype = KnowledgePromotionType(dec.decision_type)
            except ValueError:
                return False

            if dec.target_subsystem not in allowed_subsystems:
                return False

            # 3. Invalid confidence range
            if not (0.0 <= dec.confidence <= 1.0):
                return False

            # 4. Hallucinated components
            all_valid_components = set(
                u.target_component for u in incoming_updates.values()
            ) | set(e.target_component for e in active_entries.values())
            if dec.target_component not in all_valid_components:
                return False

            # 5. Duplicate target component promotion decisions
            if dec.target_component in seen_promotions:
                return False
            seen_promotions.add(dec.target_component)

            # 6. Duplicate promotion IDs
            if dec.target_entry_id:
                if dec.target_entry_id in seen_decision_ids:
                    return False
                seen_decision_ids.add(dec.target_entry_id)

            # 7. Malformed evidence / duplicate evidence IDs
            if not dec.evidence:
                return False
            seen_ev = set()
            for ev_id in dec.evidence:
                if ev_id in seen_ev:
                    return False
                seen_ev.add(ev_id)

            # 8. Invalid expected impacts
            imp = dec.expected_impact
            if not all(
                isinstance(getattr(imp, k), (int, float))
                for k in (
                    "expected_accuracy_delta",
                    "expected_latency_delta",
                    "expected_memory_delta",
                    "expected_stability_delta",
                    "expected_explainability_delta",
                )
            ):
                return False

            # 9. Promotion without accepted learning confidence
            if (
                context.latest_learning
                and not context.latest_learning.confidence_accepted
            ):
                return False

            # 10. Parent reference lineage checks
            parent_id = dec.target_entry_id
            if parent_id:
                from uuid import UUID
                from typing import Union

                parent_uuid: Union[UUID, str] = parent_id
                if isinstance(parent_id, str):
                    try:
                        parent_uuid = UUID(parent_id)
                    except ValueError:
                        parent_uuid = parent_id

                # Check key existence in active_entries mapping (which can use UUID or str)
                matched_key = None
                for k in active_entries:
                    if str(k) == str(parent_uuid):
                        matched_key = k
                        break

                if matched_key is None:
                    return False
                parent = active_entries[matched_key]

                # Circular parent references
                if parent.version.parent_entry_id == parent_id:
                    return False

                # Promotion of deprecated entries / status transitions
                if parent.status == KnowledgeStatus.DEPRECATED:
                    return False

                # safe transitions ACTIVE/EXPERIMENTAL to DEPRECATED or EXPERIMENTAL to ACTIVE
                if (
                    dtype == KnowledgePromotionType.PROMOTE_ACTIVE
                    and parent.status
                    not in (KnowledgeStatus.ACTIVE, KnowledgeStatus.EXPERIMENTAL)
                ):
                    return False

        # 11. Conflict duplicate check
        for c in parsed.conflicts:
            sig = (c.subsystem, c.component, c.parameter_name)
            if sig in seen_conflicts:
                return False
            seen_conflicts.add(sig)

        return True

    def _analyze_updates(self, context: KnowledgeContext) -> KnowledgeReasoningState:
        return self.rule_based_learner._analyze_updates(context)

    def _detect_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        return self.rule_based_learner._detect_conflicts(context, state)

    def _resolve_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        return self.rule_based_learner._resolve_conflicts(context, state)

    def _determine_promotions(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        return self.rule_based_learner._determine_promotions(context, state)

    def _version_knowledge(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        return self.rule_based_learner._version_knowledge(context, state)

    def _build_confidence(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> dict:
        return self.rule_based_learner._build_confidence(context, state)

    def _construct_session(
        self, state: KnowledgeReasoningState, confidence_details: dict
    ) -> KnowledgeSession:
        return self.rule_based_learner._construct_session(state, confidence_details)
