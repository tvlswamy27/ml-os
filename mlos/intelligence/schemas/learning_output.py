"""
LLM Learning Output Schema.

Author: Antigravity
License: MIT
"""

from pydantic import BaseModel, Field


class LLMLearningPattern(BaseModel):
    """
    Sub-schema representing a singular recurring failure or success pattern.
    """

    pattern_id: str = Field(description="Unique identifier for the pattern")
    description: str = Field(description="Description of the recurring pattern")
    frequency: int = Field(description="Number of times this pattern occurred")
    is_failure_pattern: bool = Field(
        description="Whether this represents a performance failure or degradation"
    )


class LLMLearningEvidence(BaseModel):
    """
    Sub-schema representing immutable provenance for a proposed learning update.
    """

    reflection_session_ids: list[str] = Field(
        default_factory=list, description="List of related reflection session IDs"
    )
    evaluation_session_ids: list[str] = Field(
        default_factory=list, description="List of related evaluation session IDs"
    )
    execution_session_ids: list[str] = Field(
        default_factory=list, description="List of related execution session IDs"
    )
    metrics_used: list[str] = Field(
        default_factory=list, description="Metrics monitored for this update"
    )
    confidence_values: list[float] = Field(
        default_factory=list, description="Historical confidence values"
    )
    frequency_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Execution frequency counts for components",
    )
    trend_information: dict[str, str] = Field(
        default_factory=dict, description="Metric slope and direction trends"
    )
    supporting_observations: list[str] = Field(
        default_factory=list,
        description="Any additional supporting observations text",
    )


class LLMLearningProposal(BaseModel):
    """
    Sub-schema representing a proposed permanent optimization update.
    """

    proposal_id: str = Field(description="Unique identifier for the proposal")
    update_type: str = Field(
        description="Type of learning update matching LearningUpdateType"
    )
    target_subsystem: str = Field(
        description="The subsystem targeted for learning promotion"
    )
    target_component: str = Field(
        description="The component targeted for learning promotion"
    )
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Config parameters proposed"
    )
    priority: str = Field(description="Priority level: CRITICAL, HIGH, MEDIUM, or LOW")
    evidence: LLMLearningEvidence = Field(description="Supporting provenance evidence")


class LLMLearningOutput(BaseModel):
    """
    Structured output schema for LLM-powered learning.
    """

    summary: str = Field(description="High-level text summary of the learning analysis")
    patterns: list[LLMLearningPattern] = Field(
        default_factory=list, description="Recurring patterns detected"
    )
    proposals: list[LLMLearningProposal] = Field(
        default_factory=list, description="Proposed learning updates"
    )
    confidence_score: float = Field(
        description="Confidence score in the proposals (value between 0.0 and 1.0)"
    )
    uncertainty_score: float = Field(
        description="Uncertainty score in the proposals (value between 0.0 and 1.0)"
    )
    explanation: str = Field(
        description="Details explaining confidence and uncertainty metrics"
    )
