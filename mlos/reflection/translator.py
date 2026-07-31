"""
ReflectionTranslator implementation.

Author: Antigravity
License: MIT
"""

from mlos.intelligence.schemas.reflection_output import LLMReflectionOutput
from mlos.domain.models.reflection.reflection_context import ReflectionContext
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry


class ReflectionTranslator:
    """
    Translator responsible for mapping raw LLM structured reflection output schemas
    to validated domain models.
    """

    @staticmethod
    def to_reflection_session(
        context: ReflectionContext,
        output: LLMReflectionOutput,
        telemetry: ReflectionTelemetry,
    ) -> ReflectionSession:
        """
        Translates LLMReflectionOutput into a complete ReflectionSession.
        """
        # 1. Map insights (observations and trends)
        insights = []
        for idx, obs in enumerate(output.insights):
            insights.append(
                ReflectionInsight(
                    insight_id=f"INS-OBS-{idx + 1:03d}",
                    insight_type="OBSERVATION",
                    severity="WARNING" if output.uncertainty_score > 0.5 else "INFO",
                    summary=f"Observed metric {obs.metric_key} at value {obs.value:.4f}",
                    evidence=(obs.metric_key,),
                    confidence=output.confidence_score,
                )
            )
        for idx, trend in enumerate(output.trends):
            insights.append(
                ReflectionInsight(
                    insight_id=f"INS-TRD-{idx + 1:03d}",
                    insight_type="METRIC_TREND",
                    severity="WARNING" if trend.direction == "DEGRADING" else "INFO",
                    summary=f"Trend for {trend.metric_key} is {trend.direction} (slope={trend.slope:.4f})",
                    evidence=(trend.metric_key,),
                    confidence=output.confidence_score,
                )
            )

        # 2. Map recommendations to structured feedback
        feedback = []
        for idx, rec in enumerate(output.recommendations):
            feedback.append(
                ReflectionFeedback(
                    feedback_id=f"FB-REC-{idx + 1:03d}",
                    target_subsystem=rec.target_subsystem,
                    target_component=rec.target_component,
                    action_type=rec.action_type,
                    parameters=rec.parameters,
                    priority=rec.priority,
                    reason=rec.reason,
                    expected_outcome=rec.expected_outcome,
                )
            )

        # 3. Map confidence details
        evidence_ids = tuple(ins.insight_id for ins in insights)
        accepted = (output.confidence_score >= 0.7) and (
            output.uncertainty_score <= 0.3
        )
        confidence = ReflectionConfidence(
            score=output.confidence_score,
            uncertainty=output.uncertainty_score,
            evidence=evidence_ids,
            explanation=output.explanation,
            accepted=accepted,
        )

        # 4. Construct final Session
        return ReflectionSession(
            summary=output.summary,
            insights=insights,
            feedback=feedback,
            confidence=confidence,
            telemetry=telemetry,
        )
