"""
Unit test suite for Milestone 3.5 Experiment Tracking, Registries, Lineage & Caching.

Author: Antigravity
License: MIT
"""

import pandas as pd
from sklearn.linear_model import LogisticRegression

from mlos.analysis.fingerprint import DatasetFingerprinter
from mlos.cache.cache_engine import CacheEngine
from mlos.experiment.tracker import ExperimentTracker
from mlos.observability.lineage import LineageTracker
from mlos.pipeline.registry import PipelineRegistry
from mlos.registry.model_registry import ModelRegistry


def test_dataset_fingerprint():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    fp1 = DatasetFingerprinter().compute_fingerprint(df, target_column="b")
    fp2 = DatasetFingerprinter().compute_fingerprint(df, target_column="b")
    assert fp1 == fp2
    assert len(fp1) == 64


def test_experiment_tracker(tmp_path):
    tracker = ExperimentTracker(tmp_path)
    rec = tracker.log_experiment(
        dataset_fingerprint="abc123hash",
        problem_type="binary_classification",
        pipeline_id="pipe-1",
        selected_model="Random Forest",
        candidate_models=["Logistic Regression", "Random Forest"],
        metrics={"accuracy": 0.92},
        cv_scores=[0.90, 0.94],
        training_time_s=1.2,
        prediction_time_s=0.01,
        memory_usage_mb=50.0,
        feature_importance={"f1": 0.8, "f2": 0.2},
        artifacts={"lead": "lead.csv"},
    )

    assert rec.experiment_id is not None
    fetched = tracker.get_experiment(rec.experiment_id)
    assert fetched is not None
    assert fetched["metrics"]["accuracy"] == 0.92


def test_pipeline_registry(tmp_path):
    reg = PipelineRegistry(tmp_path)
    clf = LogisticRegression()

    rec = reg.save_pipeline(
        pipeline_id="pipe-lr-01",
        pipeline_object=clf,
        model_id="logistic_regression",
        metrics={"accuracy": 0.88},
    )

    assert rec.pipeline_id == "pipe-lr-01"
    loaded = reg.load_pipeline("pipe-lr-01")
    assert loaded is not None

    all_pipes = reg.list_pipelines()
    assert len(all_pipes) == 1


def test_model_registry(tmp_path):
    reg = ModelRegistry(tmp_path)
    rec = reg.register_version(
        "logistic_regression", "1.0.0", {"accuracy": 0.89}, stage="staging"
    )

    assert rec.stage == "staging"
    ok = reg.transition_stage("logistic_regression", "1.0.0", "production")
    assert ok is True
    models = reg.list_models()
    assert models[0]["stage"] == "production"


def test_lineage_tracker(tmp_path):
    lt = LineageTracker()
    arts = lt.generate_lineage(
        output_dir=tmp_path / "lineage_test",
        dataset_fingerprint="fp123",
        features=["f1", "f2"],
        pipeline_id="p1",
        model_id="m1",
        experiment_id="e1",
        artifacts={"res": "res.json"},
    )
    assert "lineage_json" in arts
    assert "lineage_md" in arts


def test_cache_engine(tmp_path):
    cache = CacheEngine(tmp_path)
    cache.set("test_key", {"data": 123})
    res = cache.get("test_key")
    assert res == {"data": 123}
