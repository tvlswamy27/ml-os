"""
LLM Knowledge Output Schema.

Author: Antigravity
License: MIT
"""

from pydantic import BaseModel, Field


class LLMKnowledgeConflict(BaseModel):
    """
    Sub-schema representing identified parameter configuration conflicts.
    """

    conflict_id: str = Field(description="Unique conflict identifier")
    subsystem: str = Field(description="Subsystem of the conflict")
    component: str = Field(description="Component of the conflict")
    parameter_name: str = Field(description="Parameter with competing values")
    competing_values: list[str] = Field(
        default_factory=list, description="List of all competing parameter values"
    )
    resolution_applied: str = Field(
        description="Value selected to resolve the conflict"
    )


class LLMKnowledgeImpact(BaseModel):
    """
    Sub-schema representing quantitative estimated impact metrics.
    """

    expected_accuracy_delta: float = Field(
        default=0.0, description="Projected accuracy delta percentage"
    )
    expected_latency_delta: float = Field(
        default=0.0, description="Projected latency delta in milliseconds"
    )
    expected_memory_delta: float = Field(
        default=0.0, description="Projected memory footprint delta in MB"
    )
    expected_stability_delta: float = Field(
        default=0.0, description="Projected stability delta score"
    )
    expected_explainability_delta: float = Field(
        default=0.0, description="Projected explainability delta score"
    )


class LLMKnowledgePromotion(BaseModel):
    """
    Sub-schema representing a proposed promotion decision transition.
    """

    decision_type: str = Field(
        description="Must match KnowledgePromotionType enum values"
    )
    target_entry_id: str | None = Field(
        default=None, description="Existing historical target entry ID if updating"
    )
    target_component: str = Field(description="Target component name")
    target_subsystem: str = Field(description="Target subsystem name")
    promotion_reason: str = Field(description="Reason for this promotion decision")
    confidence: float = Field(description="Confidence value between 0.0 and 1.0")
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting learning update IDs or observations",
    )
    expected_impact: LLMKnowledgeImpact = Field(
        description="Quantitative delta impacts expected"
    )


class LLMKnowledgeOutput(BaseModel):
    """
    Structured output schema for LLM-powered knowledge management.
    """

    summary: str = Field(description="High-level text summary of decisions")
    promotions: list[LLMKnowledgePromotion] = Field(
        default_factory=list, description="Proposed promotion transitions"
    )
    conflicts: list[LLMKnowledgeConflict] = Field(
        default_factory=list, description="Identified and resolved conflicts"
    )
    confidence_score: float = Field(
        description="Confidence score in the decisions (value between 0.0 and 1.0)"
    )
    uncertainty_score: float = Field(
        description="Uncertainty score in the decisions (value between 0.0 and 1.0)"
    )
    explanation: str = Field(description="Details explaining metrics")
