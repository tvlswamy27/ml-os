"""
LLM Planning Output Schema.

Author: Vikram Tanakala
License: MIT
"""

from pydantic import BaseModel, Field


class LLMCandidateStrategy(BaseModel):
    """
    Sub-schema for alternative candidate strategies.
    """

    strategy_name: str = Field(description="Name of the candidate strategy")
    description: str = Field(description="Summary of what the strategy does")
    steps: list[str] = Field(
        default_factory=list,
        description="Topological pipeline steps for the strategy",
    )


class LLMPlanningOutput(BaseModel):
    """
    Structured response schema representing a complete generated execution strategy.
    """

    strategy_name: str = Field(description="Name of the selected strategy")
    strategy_description: str = Field(description="Detailed strategy description")
    topological_steps: list[str] = Field(
        default_factory=list,
        description="Ordered sequence of pipeline execution steps",
    )
    parameters: dict[str, str] = Field(
        default_factory=dict,
        description="Configuration parameters for each step",
    )
    confidence: float = Field(
        description="Confidence score for this plan (value between 0.0 and 1.0)"
    )
    reasoning: str = Field(description="Reasoning details justifying this strategy")
    alternative_candidates: list[LLMCandidateStrategy] = Field(
        default_factory=list,
        description="Alternative pipeline configurations considered",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Identified rules, assumptions, or limits constraining this plan",
    )
