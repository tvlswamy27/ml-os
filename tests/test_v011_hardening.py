import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from mlos.ui.app import app, active_runs, get_active_project_path, background_run_pipeline

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_pointer_active_project_persistence(tmp_path):
    p1 = tmp_path / "proj1"
    p2 = tmp_path / "proj2"
    (p1 / ".mlos").mkdir(parents=True)
    (p2 / ".mlos").mkdir(parents=True)

    pointer_file = Path.home() / ".mlos_active_project"

    # Store old pointer value if exists
    old_pointer = None
    if pointer_file.is_file():
        old_pointer = pointer_file.read_text(encoding="utf-8")

    try:
        # Set pointer to p1
        pointer_file.parent.mkdir(parents=True, exist_ok=True)
        pointer_file.write_text(str(p1), encoding="utf-8")
        assert get_active_project_path() == p1

        # Switch pointer to p2
        pointer_file.write_text(str(p2), encoding="utf-8")
        assert get_active_project_path() == p2

        # Test stale / invalid pointer
        pointer_file.write_text(str(tmp_path / "nonexistent"), encoding="utf-8")
        assert get_active_project_path() != tmp_path / "nonexistent"

    finally:
        # Restore pointer
        if old_pointer:
            pointer_file.write_text(old_pointer, encoding="utf-8")
        elif pointer_file.is_file():
            pointer_file.unlink()

def test_api_client_errors_4xx(client):
    # 1. Missing Content-Type for POST (Unsupported Media Type)
    response = client.post(
        "/api/project/init",
        data="invalid json",
        content_type="text/plain"
    )
    assert response.status_code == 415
    data = json.loads(response.data)
    assert data["error"]["code"] == "INVALID_REQUEST"

    # 2. Malformed JSON
    response = client.post(
        "/api/project/init",
        data="{bad json",
        content_type="application/json"
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"]["code"] == "INVALID_JSON"

    # 3. Missing required field
    response = client.post(
        "/api/project/init",
        data=json.dumps({"goal": "No Name Given"}),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"]["code"] == "INVALID_REQUEST"
    assert "name is required" in data["error"]["message"]

def test_workspace_traversal_safety(client, tmp_path):
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    (project_root / ".mlos").mkdir()

    with patch("mlos.ui.app.get_active_project_path", return_value=project_root):
        # Dataset path traversal outside workspace
        response = client.post(
            "/api/project/analyze",
            data=json.dumps({"dataset_path": "../outside.csv"}),
            content_type="application/json"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "INVALID_REQUEST"
        assert "outside workspace" in data["error"]["message"]

        # Validate dataset traversal outside workspace
        response = client.post(
            "/api/project/validate-dataset",
            data=json.dumps({"dataset_path": "../outside.csv"}),
            content_type="application/json"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["valid"] is False
        assert data["error"]["code"] == "INVALID_REQUEST"

def test_pipeline_failure_stage_preservation(tmp_path):
    project_root = tmp_path / "err_project"
    project_root.mkdir()

    run_id = "test-fail-run"
    active_runs[run_id] = {
        "status": "running",
        "current_stage": "Analysis",
        "completed_stages": [],
        "error": None,
    }

    background_run_pipeline(
        run_id=run_id,
        project_root=project_root,
        dataset_path="nonexistent.csv",
        target_column="target"
    )

    run_state = active_runs[run_id]
    assert run_state["status"] == "failed"
    assert run_state["failed_stage"] == "Analysis"
    assert "Dataset path does not exist" in run_state["error"]
