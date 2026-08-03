"""
LLM Feature Intelligence Output Schema.

Author: Antigravity
License: MIT
"""

from pydantic import BaseModel, Field


class LLMFeatureProfileOutput(BaseModel):
    """
    Sub-schema representing a feature profile.
    """

    column_name: str = Field(description="Name of the feature column")
    feature_type: str = Field(description="Detected FeatureType value")
    missing_percentage: float = Field(description="Percentage of missing values")
    variance: float = Field(description="Feature variance")
    skewness: float = Field(description="Feature skewness")
    kurtosis: float = Field(description="Feature kurtosis")
    entropy: float = Field(description="Feature entropy")
    uniqueness_ratio: float = Field(description="Unique values divided by total rows")
    duplicate_ratio: float = Field(description="Duplicate rows ratio")
    outlier_percentage: float = Field(description="Percentage of outliers")
    is_constant: bool = Field(description="Is feature constant (zero variance)")
    is_duplicate: bool = Field(description="Is feature duplicate of another column")
    is_identifier: bool = Field(description="Is feature an identifier column")
    cardinality: int = Field(description="Unique values count")


class LLMFeatureEdgeOutput(BaseModel):
    """
    Sub-schema representing an edge in the feature relationship graph.
    """

    source: str = Field(description="Source feature name")
    target: str = Field(description="Target feature name")
    edge_type: str = Field(
        description="Type of edge: correlation, redundancy, dependency, lineage"
    )
    properties: dict[str, str] = Field(
        default_factory=dict, description="Custom properties of the edge"
    )


class LLMFeatureGraphOutput(BaseModel):
    """
    Sub-schema representing the feature relationship graph.
    """

    nodes: list[str] = Field(
        default_factory=list, description="Names of all feature nodes in the graph"
    )
    edges: list[LLMFeatureEdgeOutput] = Field(
        default_factory=list, description="List of relationship edges"
    )


class LLMFeatureEngineeringProposalOutput(BaseModel):
    """
    Sub-schema representing a feature engineering proposal.
    """

    proposal_id: str = Field(description="Unique ID for the proposal")
    source_columns: list[str] = Field(
        description="Source columns for the transformation"
    )
    generated_feature: str = Field(
        description="Name of the proposed new feature column"
    )
    transformation: str = Field(description="Transformation applied")
    expected_gain: float = Field(description="Expected accuracy/performance gain")
    computational_cost: str = Field(
        description="Expected computational cost (LOW, MEDIUM, HIGH)"
    )
    confidence: float = Field(description="Confidence value between 0.0 and 1.0")
    parent_features: list[str] = Field(
        default_factory=list, description="Lineage parents"
    )


class LLMRecommendationEvidenceOutput(BaseModel):
    """
    Sub-schema representing evidence backing a recommendation.
    """

    triggered_rules: list[str] = Field(
        default_factory=list, description="List of triggered rules"
    )
    statistics_used: list[str] = Field(
        default_factory=list, description="List of statistical keys used"
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict, description="Threshold parameters evaluated"
    )
    supporting_features: list[str] = Field(
        default_factory=list, description="List of features supporting recommendation"
    )
    notes: list[str] = Field(default_factory=list, description="Explanatory notes")


class LLMFeatureRecommendationOutput(BaseModel):
    """
    Sub-schema representing a feature selection recommendation.
    """

    recommendation_id: str = Field(description="Unique ID for the recommendation")
    action: str = Field(description="Recommended action: KEEP, REMOVE, TRANSFORM, etc.")
    target_columns: list[str] = Field(description="Target columns affected")
    reasoning: str = Field(description="Explanation of recommendation")
    confidence: float = Field(description="Confidence value between 0.0 and 1.0")
    evidence: LLMRecommendationEvidenceOutput = Field(
        description="Supporting evidence DTO"
    )


class LLMFeatureOutput(BaseModel):
    """
    Structured response schema representing a complete generated Feature Intelligence session.
    """

    feature_profiles: list[LLMFeatureProfileOutput] = Field(
        default_factory=list,
        description="List of profiles for all features",
    )
    relationship_graph: LLMFeatureGraphOutput = Field(
        description="Feature relationship graph",
    )
    mutual_information_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Mutual information scores",
    )
    vif_scores: dict[str, float] = Field(
        default_factory=dict,
        description="VIF multicollinearity scores",
    )
    consensus_ranking: list[str] = Field(
        default_factory=list,
        description="Consensus ranking using Reciprocal Rank Fusion",
    )
    engineering_proposals: list[LLMFeatureEngineeringProposalOutput] = Field(
        default_factory=list,
        description="Feature engineering proposals",
    )
    selection_recommendations: list[LLMFeatureRecommendationOutput] = Field(
        default_factory=list,
        description="Feature selection recommendations",
    )
