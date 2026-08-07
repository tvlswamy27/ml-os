"""
RelationshipProfile domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.feature_intelligence.feature_graph import FeatureGraph


@dataclass(frozen=True)
class RelationshipProfile:
    """
    Captures multi-dimensional correlations, redundancies, and graph structure.
    """

    graph: FeatureGraph = field(default_factory=FeatureGraph)
    pearson_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    spearman_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    mutual_information_scores: dict[str, float] = field(default_factory=dict)
    chi_square_p_values: dict[str, dict[str, float]] = field(default_factory=dict)
    cramers_v_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    vif_scores: dict[str, float] = field(default_factory=dict)
    target_correlation: dict[str, float] = field(default_factory=dict)
    redundant_feature_groups: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
