"""
LearningTranslator implementation.

Author: Antigravity
License: MIT
"""

from mlos.intelligence.schemas.learning_output import LLMLearningOutput
from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.domain.models.learning.learning_evidence import LearningEvidence
from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry


class LearningTranslator:
    """
    Translator responsible for mapping raw LLM structured learning output schemas
    to validated domain models.
    """

    @staticmethod
    def to_learning_session(
        context: LearningContext,
        output: LLMLearningOutput,
        telemetry: LearningTelemetry,
    ) -> LearningSession:
        """
        Translates LLMLearningOutput into a complete LearningSession.
        """
        # 1. Map updates
        updates = []
        for prop in output.proposals:
            # Safely map string to LearningUpdateType enum
            try:
                ut = LearningUpdateType(prop.update_type)
            except ValueError:
                # If invalid string, keep it as is (validation will reject it)
                ut = prop.update_type  # type: ignore

            ev = prop.evidence
            evidence = LearningEvidence(
                reflection_session_ids=tuple(ev.reflection_session_ids),
                evaluation_session_ids=tuple(ev.evaluation_session_ids),
                execution_session_ids=tuple(ev.execution_session_ids),
                metrics_used=tuple(ev.metrics_used),
                confidence_values=tuple(ev.confidence_values),
                frequency_counts=dict(ev.frequency_counts),
                trend_information=dict(ev.trend_information),
                supporting_observations=tuple(ev.supporting_observations),
            )

            updates.append(
                LearningUpdate(
                    update_id=prop.proposal_id,
                    update_type=ut,
                    target_subsystem=prop.target_subsystem,
                    target_component=prop.target_component,
                    parameters=dict(prop.parameters),
                    evidence=evidence,
                )
            )

        # 2. Map confidence details
        evidence_ids = tuple(up.update_id for up in updates)
        accepted = (output.confidence_score >= 0.7) and (
            output.uncertainty_score <= 0.3
        )
        confidence = LearningConfidence(
            score=output.confidence_score,
            uncertainty=output.uncertainty_score,
            evidence=evidence_ids,
            explanation=output.explanation,
            accepted=accepted,
        )

        # 3. Construct final Session
        return LearningSession(
            summary=output.summary,
            updates=updates,
            confidence=confidence,
            telemetry=telemetry,
        )
