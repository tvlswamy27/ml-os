"""
Unit and integration tests for Milestone 3 AutoML Engine.

Author: Antigravity
License: MIT
"""

import pandas as pd

from mlos.analysis.dataset_analyzer import DatasetAnalyzer
from mlos.automl.orchestrator import AutoMLOrchestrator
from mlos.automl.preprocessing_planner import PreprocessingPlanner
from mlos.models.catalog import ModelCatalog, TaskType
from mlos.models.model_recommender import ModelRecommender


def test_model_catalog_registration():
    all_models = ModelCatalog.list_all()
    assert len(all_models) >= 15

    class_models = ModelCatalog.list_for_task(TaskType.CLASSIFICATION)
    assert any(m.model_id == "logistic_regression" for m in class_models)
    assert any(m.model_id == "random_forest_classifier" for m in class_models)

    reg_models = ModelCatalog.list_for_task(TaskType.REGRESSION)
    assert any(m.model_id == "linear_regression" for m in reg_models)


def test_dataset_analyzer_extended_intelligence():
    df = pd.DataFrame(
        {
            "id": [f"ID_{i}" for i in range(100)],
            "numeric_feat": [float(i) for i in range(100)],
            "cat_feat": ["A", "B"] * 50,
            "target": [0, 1] * 50,
        }
    )

    analyzer = DatasetAnalyzer()
    dataset = analyzer.analyze(df, target="target")

    assert dataset.rows == 100
    assert dataset.columns == 4
    assert dataset.problem_type == "binary_classification"
    assert "id" in dataset.id_columns
    assert "numeric_feat" in dataset.numerical_columns
    assert "cat_feat" in dataset.categorical_columns


def test_model_recommender():
    analyzer = DatasetAnalyzer()
    df = pd.DataFrame({"x1": range(50), "x2": range(50), "target": [0, 1] * 25})
    dataset = analyzer.analyze(df, target="target")

    recommender = ModelRecommender()
    recs = recommender.recommend(dataset)

    assert len(recs) > 0
    assert recs[0].rank == 1
    assert recs[0].is_available is True
    assert recs[0].suitability_score > 0.0


def test_preprocessing_planner():
    analyzer = DatasetAnalyzer()
    df = pd.DataFrame(
        {
            "x1": [1.0, 2.0, None, 4.0],
            "cat1": ["a", "b", "a", "b"],
            "target": [0, 1, 0, 1],
        }
    )
    dataset = analyzer.analyze(df, target="target")

    planner = PreprocessingPlanner()
    tree_meta = ModelCatalog.get("random_forest_classifier")
    assert tree_meta is not None

    plan = planner.plan_and_build(dataset, tree_meta)
    assert plan.scaling_required is False
    assert plan.transformer is not None


def test_automl_orchestrator_end_to_end(tmp_path):
    df = pd.DataFrame(
        {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )

    orchestrator = AutoMLOrchestrator(top_n_models=2, cv_folds=2)
    results, artifacts = orchestrator.run_automl(
        df, target_column="target", output_dir=tmp_path / "automl_test"
    )

    assert len(results) >= 1
    assert any(r.status == "SUCCESS" for r in results)
    assert "leaderboard_csv" in artifacts
    assert "leaderboard_json" in artifacts
    assert "leaderboard_md" in artifacts
    assert "summary_md" in artifacts
    assert "benchmark_metadata" in artifacts
