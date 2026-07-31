"""
LLM Reflection Output Schema.

Author: Antigravity
License: MIT
"""

from pydantic import BaseModel, Field


class LLMObservation(BaseModel):
    """
    Sub-schema representing a singular observed metric event.
    """

    metric_key: str = Field(description="The key of the observed metric")
    value: float = Field(description="The numeric value of the metric")
    observed_at: str = Field(
        default="", description="The execution session or timestamp of observation"
    )


class LLMTrend(BaseModel):
    """
    Sub-schema representing a performance trend over historical runs.
    """

    metric_key: str = Field(description="The metric key analyzed")
    direction: str = Field(
        description="The trend direction: IMPROVING, DEGRADING, or STABLE"
    )
    slope: float = Field(
        description="The mathematical slope/rate of change of the trend"
    )


class LLMRecommendation(BaseModel):
    """
    Sub-schema representing a corrective feedback suggestion.
    """

    target_subsystem: str = Field(description="The subsystem targeted for tuning")
    target_component: str = Field(description="The component targeted for tuning")
    action_type: str = Field(description="Action to apply, e.g., ENABLE_IMPUTATION")
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Custom parameters to configure"
    )
    priority: str = Field(description="Priority level: CRITICAL, HIGH, MEDIUM, or LOW")
    reason: str = Field(description="Detailed reason justifying this recommendation")
    expected_outcome: str = Field(
        description="Expected results after applying this action"
    )


class LLMReflectionOutput(BaseModel):
    """
    Structured output schema for LLM-powered reflection.
    """

    summary: str = Field(
        description="High-level text summary of the reflection analysis"
    )
    insights: list[LLMObservation] = Field(
        default_factory=list,
        description="Specific metric observations extracted from history",
    )
    trends: list[LLMTrend] = Field(
        default_factory=list, description="Performance trends detected"
    )
    recommendations: list[LLMRecommendation] = Field(
        default_factory=list,
        description="Feedback recommendations generated to correct regressions",
    )
    confidence_score: float = Field(
        description="Confidence score in the findings (value between 0.0 and 1.0)"
    )
    uncertainty_score: float = Field(
        description="Uncertainty estimation in the findings (value between 0.0 and 1.0)"
    )
    explanation: str = Field(
        description="Details explaining confidence and uncertainty metrics"
    )
