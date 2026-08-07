"""
LLMKnowledgeAlgorithm implementation.

Author: Antigravity
License: MIT
"""

import os
from datetime import datetime
from uuid import uuid4

from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_context import KnowledgeContext
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_promotion_decision import (
    KnowledgePromotionDecision,
    KnowledgePromotionType,
)
from mlos.domain.models.knowledge.knowledge_reasoning_state import (
    KnowledgeReasoningState,
)
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.schemas.knowledge_output import LLMKnowledgeOutput
from mlos.knowledge.algorithms.knowledge_algorithm import KnowledgeAlgorithm
from mlos.knowledge.translator import KnowledgeTranslator


class LLMKnowledgeAlgorithm(KnowledgeAlgorithm):
    """
    LLM-powered knowledge management algorithm.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize LLM knowledge learner.
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
        self._last_parsed_output: LLMKnowledgeOutput | None = None
        self._last_telemetry: KnowledgeTelemetry | None = None
        self._current_context: KnowledgeContext | None = None
        self._promotion_decisions: list[KnowledgePromotionDecision] = []

    def can_manage(self, context: KnowledgeContext) -> bool:
        """
        LLM management is always capable.
        """
        return True

    def manage(self, context: KnowledgeContext) -> KnowledgeSession:
        """
        Executes LLM request and builds session.
        """
        self._current_context = context

        response = self.intelligence_service.execute_subsystem(
            "knowledge", context, LLMKnowledgeOutput
        )

        if not response.validation_passed or response.parsed_output is None:
            raise ValueError(
                f"LLM Knowledge management failed: {response.raw_response}"
            )

        self._last_parsed_output = response.parsed_output
        self._promotion_decisions = KnowledgeTranslator.to_promotion_decisions(
            response.parsed_output
        )

        token_usage = {}
        if response.call_metrics and response.call_metrics.token_usage:
            tu = response.call_metrics.token_usage
            token_usage = {
                "input_tokens": tu.input_tokens,
                "output_tokens": tu.output_tokens,
                "total_tokens": tu.total_tokens,
            }

        self._last_telemetry = KnowledgeTelemetry(
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

        # Run template method stages
        return super().manage(context)

    def _analyze_updates(self, context: KnowledgeContext) -> KnowledgeReasoningState:
        """
        Step 1: Programmatic parsing of learning updates.
        """
        from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
            RuleBasedKnowledgeAlgorithm,
        )

        rb = RuleBasedKnowledgeAlgorithm()
        return rb._analyze_updates(context)

    def _detect_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """
        Step 2: Scans incoming updates against existing entries.
        """
        from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
            RuleBasedKnowledgeAlgorithm,
        )

        rb = RuleBasedKnowledgeAlgorithm()
        return rb._detect_conflicts(context, state)

    def _resolve_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """
        Step 3: Resolves configuration conflicts.
        """
        from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
            RuleBasedKnowledgeAlgorithm,
        )

        rb = RuleBasedKnowledgeAlgorithm()
        return rb._resolve_conflicts(context, state)

    def _determine_promotions(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """
        Step 4: Determine promotions from translated decisions.
        """
        promoted_entries = []

        for dec in self._promotion_decisions:
            if dec.decision_type in (
                KnowledgePromotionType.KEEP_EXISTING,
                KnowledgePromotionType.REJECT,
            ):
                continue

            matching_update = None
            for u in state.incoming_updates:
                if (
                    u.target_subsystem == dec.target_subsystem
                    and u.target_component == dec.target_component
                ):
                    matching_update = u
                    break

            if matching_update is None:
                continue

            status = (
                KnowledgeStatus.ACTIVE
                if dec.decision_type == KnowledgePromotionType.PROMOTE_ACTIVE
                else (
                    KnowledgeStatus.DEPRECATED
                    if dec.decision_type == KnowledgePromotionType.DEPRECATE
                    else KnowledgeStatus.EXPERIMENTAL
                )
            )

            entry = KnowledgeEntry(
                knowledge_id=matching_update.update_id,
                knowledge_type=matching_update.entry_type,
                target_subsystem=dec.target_subsystem,
                target_component=dec.target_component,
                parameters=dict(matching_update.parameters),
                source_learning_sessions=(matching_update.learning_session_id,),
                evidence_summary=matching_update.evidence_summary,
                version=KnowledgeVersion(
                    version_number=1,
                    parent_entry_id=dec.target_entry_id,
                    timestamp=datetime.now(),
                    change_summary="",
                    reason=dec.promotion_reason,
                ),
                created_at=datetime.now(),
                last_used=None,
                usage_count=0,
                confidence=KnowledgeConfidence(
                    score=dec.confidence,
                    uncertainty=1.0 - dec.confidence,
                    support_count=1,
                    usage_history_count=0,
                    explanation=dec.promotion_reason,
                ),
                status=status,
            )
            promoted_entries.append(entry)

        return KnowledgeReasoningState(
            incoming_updates=state.incoming_updates,
            detected_conflicts=state.detected_conflicts,
            resolved_entries=tuple(promoted_entries),
            current_max_version=state.current_max_version,
        )

    def _version_knowledge(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """
        Step 5: Apply append-only version lineage tracking.
        """
        final_entries = []

        existing_entries = []
        if context.existing_knowledge is not None:
            existing_entries = list(context.existing_knowledge.active_entries)

        for temp_entry in state.resolved_entries:
            parent_entry = None
            parent_id = temp_entry.version.parent_entry_id
            if parent_id:
                for old in existing_entries:
                    if old.knowledge_id == parent_id:
                        parent_entry = old
                        break
            else:
                for old in existing_entries:
                    if (
                        old.target_component == temp_entry.target_component
                        and old.knowledge_type == temp_entry.knowledge_type
                        and old.status
                        in (KnowledgeStatus.ACTIVE, KnowledgeStatus.EXPERIMENTAL)
                    ):
                        parent_entry = old
                        break

            if parent_entry is not None:
                new_ver_num = parent_entry.version.version_number + 1
                parent_id = parent_entry.knowledge_id
            else:
                new_ver_num = 1
                parent_id = None

            version_meta = KnowledgeVersion(
                version_number=new_ver_num,
                parent_entry_id=parent_id,
                timestamp=datetime.now(),
                change_summary=f"LLM promoted update to version {new_ver_num}.",
                reason=temp_entry.version.reason or temp_entry.evidence_summary,
            )

            promoted_entry = KnowledgeEntry(
                knowledge_id=str(uuid4()),
                knowledge_type=temp_entry.knowledge_type,
                target_subsystem=temp_entry.target_subsystem,
                target_component=temp_entry.target_component,
                parameters=dict(temp_entry.parameters),
                source_learning_sessions=temp_entry.source_learning_sessions,
                evidence_summary=temp_entry.evidence_summary,
                version=version_meta,
                created_at=datetime.now(),
                last_used=None,
                usage_count=0,
                confidence=temp_entry.confidence,
                status=temp_entry.status,
            )
            final_entries.append(promoted_entry)

        return KnowledgeReasoningState(
            incoming_updates=state.incoming_updates,
            detected_conflicts=state.detected_conflicts,
            resolved_entries=tuple(final_entries),
            current_max_version=state.current_max_version,
        )

    def _build_confidence(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> dict:
        """
        Step 6: Dict details details mapping.
        """
        return {}

    def _construct_session(
        self, state: KnowledgeReasoningState, confidence_details: dict
    ) -> KnowledgeSession:
        """
        Step 7: Assembles variables.
        """
        if not self._last_parsed_output or not self._last_telemetry:
            raise ValueError("No LLM knowledge output or telemetry cached.")

        context = self._current_context
        if context is None:
            context = KnowledgeContext(
                project_name="unknown",
                project_goal="unknown",
                latest_learning=None,
            )

        session = KnowledgeTranslator.to_knowledge_session(
            context=context,
            output=self._last_parsed_output,
            telemetry=self._last_telemetry,
        )

        return KnowledgeSession(
            summary=session.summary,
            promoted_entries=list(state.resolved_entries),
            conflicts=session.conflicts,
            telemetry=self._last_telemetry,
        )
