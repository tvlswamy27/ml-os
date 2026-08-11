"""
Unit and integration tests verifying ML-OS UI v0.1 metadata consistency and experiment tracking fixes.

Author: Antigravity
License: MIT
"""

import json
from pathlib import Path
import pandas as pd
import pytest
from mlos.sdk.project import MLProject
from mlos.engine.engine import MLOSEngine
from mlos.experiment.tracker import ExperimentTracker
from mlos.experiment.ids import generate_experiment_id


def test_centralized_experiment_id_generation():
    id1 = generate_experiment_id()
    id2 = generate_experiment_id()
    assert id1 != id2
    assert len(id1) == 8


def test_workspace_isolation_and_tracking(tmp_path):
    # Setup temporary workspace
    project_root = tmp_path / "my_project"
    project_root.mkdir()

    # 1. Initialize project
    project = MLProject(
        name="TestProject", goal="Test Goal", project_path=str(project_root)
    )

    # 2. Write dummy CSV with 15 rows to satisfy default CV folding
    df = pd.DataFrame(
        {
            "Age": [22, 38, 26, 35, 54, 23, 45, 67, 12, 34, 56, 78, 90, 11, 22],
            "Fare": [
                7.25,
                71.83,
                7.92,
                53.1,
                8.05,
                12.0,
                4.0,
                50.0,
                9.0,
                15.0,
                8.0,
                100.0,
                20.0,
                7.0,
                10.0,
            ],
            "Survived": [0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    csv_path = project_root / "dummy.csv"
    df.to_csv(csv_path, index=False)

    # Analyze first to populate problem type
    engine = MLOSEngine()
    engine.project_memory = project.memory
    report = engine.run_analysis(str(csv_path), "Survived")
    project.save()

    # Assert problem type is "Binary Classification" in profile and dataset (Test 4)
    assert project.memory.project_profile.problem_type == "Binary Classification"
    assert project.memory.dataset.problem_type == "Binary Classification"

    # 3. First pipeline run
    exp_id_1 = generate_experiment_id()
    session1 = project.run(experiment_id=exp_id_1)

    # Run AutoML
    results1, artifacts1 = engine.run_automl(
        str(csv_path),
        target_column="Survived",
        output_dir=str(project_root / "artifacts" / "automl"),
        experiment_id=exp_id_1,
        workspace_root=project_root,
    )

    # Assert files are created inside the temp project root (Test 7)
    assert (project_root / ".mlos" / "experiments" / "experiments.json").is_file()
    assert (project_root / ".mlos" / "model_registry" / "model_registry.json").is_file()

    tracker = ExperimentTracker(project_root)
    exps = tracker.list_experiments()

    # Test 1: One pipeline run creates exactly one experiment
    assert len(exps) == 1

    # Test 3: One experiment contains both lifecycle and AutoML data
    exp = exps[0]
    assert exp["experiment_id"] == exp_id_1
    assert exp["name"] == "TestProject"
    assert exp["problem_type"] == "Binary Classification"
    assert exp["selected_model"] != "None"
    assert "runs" in exp
    assert len(exp["runs"]) == 1
    assert exp["runs"][0]["metadata"]["experiment_id"] == exp_id_1
    assert exp["runs"][0]["metadata"]["project_name"] == "TestProject"
    assert exp["runs"][0]["metadata"]["problem_type"] == "Binary Classification"

    # Test 5: No duplicate Model=None experiment
    assert exp["selected_model"] is not None
    assert exp["selected_model"] != "None"

    # 4. Second pipeline run
    exp_id_2 = generate_experiment_id()
    session2 = project.run(experiment_id=exp_id_2)
    results2, artifacts2 = engine.run_automl(
        str(csv_path),
        target_column="Survived",
        output_dir=str(project_root / "artifacts" / "automl"),
        experiment_id=exp_id_2,
        workspace_root=project_root,
    )

    # Test 2: Two pipeline runs create exactly two experiments with different IDs
    tracker_reload = ExperimentTracker(project_root)
    exps2 = tracker_reload.list_experiments()
    assert len(exps2) == 2

    ids = [e["experiment_id"] for e in exps2]
    assert exp_id_1 in ids
    assert exp_id_2 in ids
    assert exp_id_1 != exp_id_2


def test_confidence_formatting_data():
    from mlos.decision.strategies.train_test_split_decision import (
        TrainTestSplitDecision,
    )

    # Verify that python decision confidence is a string (e.g. "High" or percentage)
    strategy = TrainTestSplitDecision()
    decisions = strategy.decide(None)
    assert len(decisions) == 1
    assert decisions[0].confidence == "High"
