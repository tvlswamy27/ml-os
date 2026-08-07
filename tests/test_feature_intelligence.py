"""
Unit tests for the Feature Intelligence subsystem algorithms and stages.

Author: Antigravity
License: MIT
"""

import pandas as pd

from mlos.domain.enums.feature_type import FeatureType
from mlos.domain.enums.recommendation_action import RecommendationAction
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.feature_intelligence import (
    FeatureContext,
    FeatureReasoningState,
)
from mlos.feature_intelligence.algorithms.rule_based_feature_algorithm import (
    RuleBasedFeatureAlgorithm,
)


def test_rule_based_feature_discovery():
    """
    Verify that rule-based algorithm correctly discovers column types and target leakage.
    """
    # 1. Setup mock DataFrame
    df = pd.DataFrame(
        {
            "id_col": [1, 2, 3, 4, 5],
            "num_col": [10.5, 20.1, 15.3, 12.0, 18.9],
            "cat_col": ["low", "high", "medium", "low", "high"],
            "bool_col": [True, False, True, True, False],
            "date_col": pd.date_range("2026-08-01", periods=5),
            "target": [0, 1, 0, 0, 1],
            "target_leak": [0, 1, 0, 0, 1],  # 100% correlation with target
        }
    )

    dataset = Dataset(
        path="dummy.csv",
        target="target",
        problem_type="classification",
    )
    context = FeatureContext(
        project_name="TestProj",
        project_goal="Test discovery",
        dataset=dataset,
    )

    algo = RuleBasedFeatureAlgorithm()
    state = FeatureReasoningState()

    # Run discovery stage
    algo._discover_features(context, df, state)

    # Check discovered types
    assert state.facts["type_id_col"] == FeatureType.IDENTIFIER.value
    assert state.facts["type_num_col"] == FeatureType.NUMERIC.value
    assert state.facts["type_cat_col"] == FeatureType.CATEGORICAL.value
    assert state.facts["type_bool_col"] == FeatureType.BOOLEAN.value
    assert state.facts["type_date_col"] == FeatureType.DATETIME.value

    # Check target leakage detection
    assert "target_leak" in state.target_leakage_candidates
    assert "num_col" not in state.target_leakage_candidates


def test_rule_based_profiling_and_statistics():
    """
    Verify that profiling stage correctly computes statistics, quality scores, and profiles.
    """
    df = pd.DataFrame(
        {
            "normal_col": [10, 20, 15, 12, 18],
            "constant_col": [5, 5, 5, 5, 5],
            "skewed_col": [1, 2, 3, 10, 100],  # Outliers / skewed
        }
    )

    dataset = Dataset(
        path="dummy.csv",
        numerical_columns=["normal_col", "constant_col", "skewed_col"],
    )
    context = FeatureContext(
        project_name="TestProj",
        project_goal="Test profiling",
        dataset=dataset,
    )

    algo = RuleBasedFeatureAlgorithm()
    state = FeatureReasoningState()

    # Pre-populate types
    state.facts["type_normal_col"] = FeatureType.NUMERIC.value
    state.facts["type_constant_col"] = FeatureType.NUMERIC.value
    state.facts["type_skewed_col"] = FeatureType.NUMERIC.value

    algo._profile_features(context, df, state)

    # Check constant column identification
    assert state.feature_profiles["constant_col"].is_constant is True
    assert state.feature_profiles["normal_col"].is_constant is False

    # Check skewness and kurtosis calculations
    skewed_stats = state.feature_profiles["skewed_col"].statistics
    assert skewed_stats.variance > 0
    assert skewed_stats.skewness != 0.0


def test_rule_based_relationships_and_graph():
    """
    Verify relationship analysis computes Pearson/Spearman/VIF matrices and builds FeatureGraph.
    """
    df = pd.DataFrame(
        {
            "col1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "col2": [2.0, 4.0, 6.0, 8.0, 10.0],  # Highly correlated (Pearson = 1.0)
            "col3": [5.0, 2.0, 9.0, 1.0, 4.0],
        }
    )

    dataset = Dataset(
        path="dummy.csv",
        numerical_columns=["col1", "col2", "col3"],
    )
    context = FeatureContext(
        project_name="TestProj",
        project_goal="Test relationships",
        dataset=dataset,
    )

    algo = RuleBasedFeatureAlgorithm()
    state = FeatureReasoningState()

    # Profile first to create profiles needed by relationship stage
    for col in df.columns:
        state.facts[f"type_{col}"] = FeatureType.NUMERIC.value

    algo._profile_features(context, df, state)
    algo._analyze_relationships(context, df, state)

    # Check correlation matrix
    assert state.relationship_profile.pearson_matrix["col1"]["col2"] == 1.0

    # Check redundant group detection
    assert ("col1", "col2") in state.relationship_profile.redundant_feature_groups or (
        "col2",
        "col1",
    ) in state.relationship_profile.redundant_feature_groups

    # Check graph construction
    graph = state.relationship_profile.graph
    assert "col1" in graph.nodes
    assert "col2" in graph.nodes
    assert len(graph.edges) >= 2  # correlation + redundancy edges


def test_rule_based_ranking_rrf():
    """
    Verify pluggable ranking strategies output rankings and RRF calculates consensus ranking.
    """
    df = pd.DataFrame(
        {
            "col1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "col2": [5.0, 2.0, 9.0, 1.0, 4.0],
            "target": [1, 2, 3, 4, 5],
        }
    )

    dataset = Dataset(
        path="dummy.csv",
        numerical_columns=["col1", "col2"],
        target="target",
        problem_type="regression",
    )
    context = FeatureContext(
        project_name="TestProj",
        project_goal="Test ranking",
        dataset=dataset,
    )

    algo = RuleBasedFeatureAlgorithm()
    state = FeatureReasoningState()

    for col in df.columns:
        state.facts[f"type_{col}"] = FeatureType.NUMERIC.value

    algo._profile_features(context, df, state)
    algo._analyze_relationships(context, df, state)

    ranking_profile = algo._rank_features(context, df, state)

    # Verify consensus ranking and individual profiles are filled
    assert ranking_profile.consensus_rrf
    assert "col1" in ranking_profile.consensus_rrf


def test_rule_based_engineering_and_selection():
    """
    Verify selection recommendations and engineering proposals are correctly formulated.
    """
    df = pd.DataFrame(
        {
            "skewed_col": [1, 2, 3, 10, 100],  # skewness > 1.5
            "constant_col": [5, 5, 5, 5, 5],
            "normal_col": [10, 20, 15, 12, 18],
            "target": [0, 1, 0, 0, 1],
        }
    )

    dataset = Dataset(
        path="dummy.csv",
        numerical_columns=["skewed_col", "constant_col", "normal_col"],
        target="target",
        problem_type="classification",
    )
    context = FeatureContext(
        project_name="TestProj",
        project_goal="Test selection",
        dataset=dataset,
    )

    algo = RuleBasedFeatureAlgorithm()
    state = FeatureReasoningState()

    for col in df.columns:
        state.facts[f"type_{col}"] = FeatureType.NUMERIC.value

    algo._profile_features(context, df, state)
    algo._analyze_relationships(context, df, state)
    ranking = algo._rank_features(context, df, state)

    proposals = algo._recommend_engineering(context, df, state)
    recommendations = algo._select_features(context, ranking, state)

    # Verify engineering log proposal exists for skewed_col
    skewed_props = [p for p in proposals if "skewed_col" in p.source_columns]
    assert skewed_props
    assert skewed_props[0].transformation in ("log", "log1p")

    # Verify recommendations
    rec_map = {r.target_columns[0]: r for r in recommendations}

    # Constant column should be REMOVE
    assert rec_map["constant_col"].action == RecommendationAction.REMOVE
    # Evidence triggered rules should be present
    assert "constant_column_filter" in rec_map["constant_col"].evidence.triggered_rules

    # Normal column should be KEEP
    assert rec_map["normal_col"].action == RecommendationAction.KEEP
