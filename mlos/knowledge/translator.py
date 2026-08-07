"""
KnowledgeTranslator implementation.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict
from mlos.domain.models.knowledge.knowledge_context import KnowledgeContext
from mlos.domain.models.knowledge.knowledge_promotion_decision import (
    KnowledgeImpact,
    KnowledgePromotionDecision,
    KnowledgePromotionType,
)
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry
from mlos.intelligence.schemas.knowledge_output import LLMKnowledgeOutput


class KnowledgeTranslator:
    """
    Translator responsible for mapping LLM structured knowledge schemas to domain objects.
    """

    @staticmethod
    def to_promotion_decisions(
        output: LLMKnowledgeOutput,
    ) -> list[KnowledgePromotionDecision]:
        """
        Translates promotions in LLMKnowledgeOutput to domain KnowledgePromotionDecision list.
        """
        decisions = []
        for p in output.promotions:
            try:
                dtype = KnowledgePromotionType(p.decision_type)
            except ValueError:
                dtype = p.decision_type  # type: ignore

            imp = p.expected_impact
            impact = KnowledgeImpact(
                expected_accuracy_delta=imp.expected_accuracy_delta,
                expected_latency_delta=imp.expected_latency_delta,
                expected_memory_delta=imp.expected_memory_delta,
                expected_stability_delta=imp.expected_stability_delta,
                expected_explainability_delta=imp.expected_explainability_delta,
            )

            decisions.append(
                KnowledgePromotionDecision(
                    decision_type=dtype,
                    target_entry_id=p.target_entry_id,
                    target_component=p.target_component,
                    target_subsystem=p.target_subsystem,
                    promotion_reason=p.promotion_reason,
                    confidence=p.confidence,
                    evidence=tuple(p.evidence),
                    expected_impact=impact,
                )
            )
        return decisions

    @staticmethod
    def to_conflicts(output: LLMKnowledgeOutput) -> list[KnowledgeConflict]:
        """
        Translates conflicts in LLMKnowledgeOutput to domain KnowledgeConflict list.
        """
        conflicts = []
        for c in output.conflicts:
            conflicts.append(
                KnowledgeConflict(
                    conflict_id=c.conflict_id,
                    subsystem=c.subsystem,
                    component=c.component,
                    parameter_name=c.parameter_name,
                    competing_values=tuple(c.competing_values),
                    resolution_applied=c.resolution_applied,
                )
            )
        return conflicts

    @staticmethod
    def to_knowledge_session(
        context: KnowledgeContext,
        output: LLMKnowledgeOutput,
        telemetry: KnowledgeTelemetry,
    ) -> KnowledgeSession:
        """
        Translates LLMKnowledgeOutput into a KnowledgeSession.
        Does NOT build KnowledgeEntry objects directly (this is handled by KnowledgeAlgorithm).
        """
        conflicts = KnowledgeTranslator.to_conflicts(output)
        return KnowledgeSession(
            summary=output.summary,
            promoted_entries=[],  # Excludes promoted entries (algorithm populates this)
            conflicts=conflicts,
            telemetry=telemetry,
        )
