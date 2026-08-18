"""
Unit and integration tests for the ML-OS UI Flask server endpoints.

Author: Antigravity
License: MIT
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from mlos.cli.commands.ui import UICommand
from mlos.ui.app import app, active_runs


@pytest.fixture
def client(tmp_path):
    """A flask test client configured with a temporary workspace."""
    app.config["TESTING"] = True

    # We mock get_active_project_path in app.py to return tmp_path
    with patch("mlos.ui.app.get_active_project_path", return_value=tmp_path):
        with app.test_client() as client:
            yield client


def test_ui_command_registration():
    """Verify that UICommand is properly registered."""
    cmd = UICommand()
    assert cmd.name == "ui"
    assert "Start the local ML-OS Web UI workspace." in cmd.help
    assert cmd.epilog != ""


def test_index_route(client):
    """Verify the root index page renders successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"ML-OS Studio" in response.data


def test_api_project_uninitialized(client):
    """Verify project API response when workspace is empty."""
    response = client.get("/api/project")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "no_project"
    assert "project_path" in data


def test_api_project_init(client, tmp_path):
    """Verify project initialization via API."""
    response = client.post(
        "/api/project/init",
        data=json.dumps(
            {"name": "TestProject", "goal": "Minimize MSE", "path": str(tmp_path)}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "Successfully initialized project" in data["message"]
    assert data["project_path"] == str(tmp_path)

    # Verify .mlos directory was created
    assert (tmp_path / ".mlos").is_dir()
    assert (tmp_path / ".mlos" / "project_config.yaml").is_file()


def test_api_project_active(client, tmp_path):
    """Verify project API response when project is active."""
    # First initialize
    client.post(
        "/api/project/init",
        data=json.dumps(
            {"name": "TestProject", "goal": "Minimize MSE", "path": str(tmp_path)}
        ),
        content_type="application/json",
    )

    # Get status
    response = client.get("/api/project")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "active"
    assert data["project_name"] == "TestProject"
    assert data["project_goal"] == "Minimize MSE"


def test_api_project_analyze(client, tmp_path):
    """Verify dataset analysis endpoint handles data correctly."""
    # 1. Initialize project
    client.post(
        "/api/project/init",
        data=json.dumps(
            {"name": "AnalysisProject", "goal": "Test Analysis", "path": str(tmp_path)}
        ),
        content_type="application/json",
    )

    # 2. Write a dummy CSV file
    df = pd.DataFrame(
        {
            "Age": [22, 38, 26, 35, 54],
            "Fare": [7.25, 71.83, 7.92, 53.1, 8.05],
            "Survived": [0, 1, 1, 1, 0],
        }
    )
    csv_path = tmp_path / "dummy.csv"
    df.to_csv(csv_path, index=False)

    # 3. Request analysis
    response = client.post(
        "/api/project/analyze",
        data=json.dumps({"dataset_path": str(csv_path), "target_column": "Survived"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)

    # Validate returned analysis data
    summary = data["dataset_summary"]
    assert summary["rows"] == 5
    assert summary["columns"] == 3
    assert summary["target"] == "Survived"

    features = data["features"]
    assert "Age" in features["numerical"]
    assert "Fare" in features["numerical"]

    intel = data["problem_intelligence"]
    assert "problem_type" in intel
    assert len(intel["baseline_models"]) > 0


def test_api_run_pipeline_flow(client, tmp_path):
    """Verify background running status tracking and results retrieval."""
    # 1. Initialize project
    client.post(
        "/api/project/init",
        data=json.dumps(
            {"name": "RunProject", "goal": "Test Running", "path": str(tmp_path)}
        ),
        content_type="application/json",
    )

    # 2. Write dummy CSV
    df = pd.DataFrame(
        {
            "Age": [22, 38, 26, 35, 54],
            "Fare": [7.25, 71.83, 7.92, 53.1, 8.05],
            "Survived": [0, 1, 1, 1, 0],
        }
    )
    csv_path = tmp_path / "dummy.csv"
    df.to_csv(csv_path, index=False)

    # 3. Post run request
    response = client.post(
        "/api/project/run",
        data=json.dumps({"dataset_path": str(csv_path), "target_column": "Survived"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    run_id = data["run_id"]
    assert run_id is not None

    # Wait or poll status (Since it runs asynchronously, check initial state in active_runs)
    assert run_id in active_runs
    status_response = client.get(f"/api/project/run/status/{run_id}")
    assert status_response.status_code == 200
    status_data = json.loads(status_response.data)
    assert status_data["status"] in ["queued", "running", "completed", "success"]


def test_api_experiments_listing(client, tmp_path):
    """Verify listing and detail querying of experiments."""
    # Create mock experiments data inside tmp_path
    from mlos.experiment.tracker import ExperimentTracker

    tracker = ExperimentTracker(tmp_path)
    tracker.log_experiment(
        dataset_fingerprint="dummy_hash_123",
        problem_type="Binary Classification",
        pipeline_id="pipe_rf_01",
        selected_model="Random Forest",
        candidate_models=["Logistic Regression", "Random Forest"],
        metrics={"accuracy": 0.85},
        cv_scores=[0.82, 0.88],
        training_time_s=1.5,
        prediction_time_s=0.02,
        memory_usage_mb=40.0,
        feature_importance={"Age": 0.6, "Fare": 0.4},
        artifacts={"model": "model.joblib"},
        experiment_id="exp-test-id",
    )

    # Test list experiments endpoint
    response = client.get("/api/experiments")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["experiment_id"] == "exp-test-id"
    assert data[0]["selected_model"] == "Random Forest"
    assert data[0]["metrics"]["accuracy"] == 0.85

    # Test single experiment details endpoint
    detail_response = client.get("/api/experiments/exp-test-id")
    assert detail_response.status_code == 200
    detail_data = json.loads(detail_response.data)
    assert detail_data["experiment_id"] == "exp-test-id"
    assert detail_data["hyperparameters"] == {}


def test_api_experiments_comparison(client, tmp_path):
    """Verify comparing two experiments side-by-side."""
    from mlos.experiment.tracker import ExperimentTracker

    tracker = ExperimentTracker(tmp_path)

    # Log exp1
    tracker.log_experiment(
        dataset_fingerprint="dummy_hash_123",
        problem_type="Binary Classification",
        pipeline_id="pipe1",
        selected_model="Random Forest",
        candidate_models=["Random Forest"],
        metrics={"accuracy": 0.85, "f1": 0.83},
        cv_scores=[0.85],
        training_time_s=1.0,
        prediction_time_s=0.01,
        memory_usage_mb=30.0,
        feature_importance={},
        artifacts={},
        experiment_id="exp1",
    )

    # Log exp2
    tracker.log_experiment(
        dataset_fingerprint="dummy_hash_123",
        problem_type="Binary Classification",
        pipeline_id="pipe2",
        selected_model="Logistic Regression",
        candidate_models=["Logistic Regression"],
        metrics={"accuracy": 0.75, "f1": 0.70},
        cv_scores=[0.75],
        training_time_s=0.5,
        prediction_time_s=0.005,
        memory_usage_mb=10.0,
        feature_importance={},
        artifacts={},
        experiment_id="exp2",
    )

    # Compare them
    response = client.post(
        "/api/experiments/compare",
        data=json.dumps({"exp1": "exp1", "exp2": "exp2"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)

    comparisons = data["metric_comparison"]
    assert comparisons["accuracy"]["exp1"] == 0.85
    assert comparisons["accuracy"]["exp2"] == 0.75
    assert comparisons["accuracy"]["diff"] == -0.10
