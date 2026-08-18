import pytest
import time
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import pandas as pd
from unittest.mock import MagicMock

from mlos.communication.event_bus import GlobalEventBus, ExecutionEvent
from mlos.execution.exceptions import ExecutionCancelledError
from mlos.execution_intelligence.runtime import ExecutionRuntime, ExecutionGraph, ExecutionStage
from mlos.sdk.project import MLProject
from mlos.engine.engine import MLOSEngine
from mlos.ui.app import app, active_runs, background_run_pipeline, active_runs_lock


@pytest.fixture
def clean_event_bus():
    bus = GlobalEventBus()
    bus.clear()
    yield bus
    bus.clear()


@pytest.fixture
def clean_active_runs():
    with active_runs_lock:
        active_runs.clear()
    yield
    with active_runs_lock:
        active_runs.clear()


# Test 1 — Cancellation registry
def test_cancellation_registry(clean_event_bus):
    run_id = "test-run-123"
    assert clean_event_bus.is_cancel_requested(run_id) is False

    clean_event_bus.request_cancel(run_id)
    assert clean_event_bus.is_cancel_requested(run_id) is True

    clean_event_bus.clear_cancel_request(run_id)
    assert clean_event_bus.is_cancel_requested(run_id) is False


# Test 2 — Run ID isolation
def test_run_id_isolation(clean_event_bus):
    events_a = []
    events_b = []

    def cb_a(event):
        if event.run_id == "run-A":
            events_a.append(event)

    def cb_b(event):
        if event.run_id == "run-B":
            events_b.append(event)

    clean_event_bus.subscribe("*", cb_a)
    clean_event_bus.subscribe("*", cb_b)

    clean_event_bus.publish("TestEvent", "SourceA", {"data": 1}, run_id="run-A")
    clean_event_bus.publish("TestEvent", "SourceB", {"data": 2}, run_id="run-B")

    assert len(events_a) == 1
    assert events_a[0].run_id == "run-A"
    assert len(events_b) == 1
    assert events_b[0].run_id == "run-B"


# Test 3 — Stage events
class MockStage(ExecutionStage):
    def __init__(self, name_str):
        self._name = name_str

    @property
    def name(self) -> str:
        return self._name

    def execute(self, memory, context):
        return "mocked result"


def test_stage_events_correlation(clean_event_bus):
    run_id = "run-stage-test"
    graph = ExecutionGraph()
    stage = MockStage("Data Loading")
    graph.add_stage(stage)

    memory_mock = MagicMock()
    runtime = ExecutionRuntime()

    events = []
    clean_event_bus.subscribe("*", lambda e: events.append(e) if e.run_id == run_id else None)

    runtime.run_graph(graph, memory_mock, dataset_path="test.csv", target="target", run_id=run_id)

    stage_started = [e for e in events if e.event_type == "StageStarted"]
    stage_completed = [e for e in events if e.event_type == "StageCompleted"]

    assert len(stage_started) == 1
    assert stage_started[0].payload["stage"] == "Data Loading"
    assert stage_started[0].run_id == run_id

    assert len(stage_completed) == 1
    assert stage_completed[0].payload["stage"] == "Data Loading"
    assert stage_completed[0].run_id == run_id


# Test 4 — Completion
def test_execution_completion(clean_event_bus):
    run_id = "run-completion-test"
    graph = ExecutionGraph()
    graph.add_stage(MockStage("Data Loading"))

    memory_mock = MagicMock()
    runtime = ExecutionRuntime()

    events = []
    clean_event_bus.subscribe("*", lambda e: events.append(e) if e.run_id == run_id else None)

    runtime.run_graph(graph, memory_mock, dataset_path="test.csv", target="target", run_id=run_id)

    completed_events = [e for e in events if e.event_type == "ExecutionCompleted"]
    assert len(completed_events) == 1
    assert completed_events[0].run_id == run_id


# Test 5 — Failure
class FailureStage(ExecutionStage):
    @property
    def name(self) -> str:
        return "Failing Stage"

    def execute(self, memory, context):
        raise ValueError("Controlled Stage Failure")


def test_execution_failure_handling(clean_event_bus):
    run_id = "run-failure-test"
    graph = ExecutionGraph()
    stage1 = MockStage("Data Loading")
    stage2 = FailureStage()
    stage3 = MockStage("Transformation")
    
    graph.add_stage(stage1)
    graph.add_stage(stage2)
    graph.add_stage(stage3)

    graph.add_dependency("Failing Stage", "Data Loading")
    graph.add_dependency("Transformation", "Failing Stage")

    memory_mock = MagicMock()
    runtime = ExecutionRuntime()

    events = []
    clean_event_bus.subscribe("*", lambda e: events.append(e) if e.run_id == run_id else None)

    with pytest.raises(ValueError, match="Controlled Stage Failure"):
        runtime.run_graph(graph, memory_mock, dataset_path="test.csv", target="target", run_id=run_id)

    # Verify stage failed event was published
    failed_stages = [e for e in events if e.event_type == "StageFailed"]
    assert len(failed_stages) == 1
    assert failed_stages[0].payload["stage"] == "Failing Stage"

    # Verify execution failed event was published
    failed_executions = [e for e in events if e.event_type == "ExecutionFailed"]
    assert len(failed_executions) == 1

    # Verify stage 3 (Transformation) never executed (no StageStarted)
    started_transformation = [e for e in events if e.event_type == "StageStarted" and e.payload["stage"] == "Transformation"]
    assert len(started_transformation) == 0


# Test 6 — Cancellation before stage
def test_cancellation_before_stage(clean_event_bus):
    run_id = "run-cancel-test"
    graph = ExecutionGraph()
    graph.add_stage(MockStage("Data Loading"))
    graph.add_stage(MockStage("Validation"))
    graph.add_dependency("Validation", "Data Loading")

    memory_mock = MagicMock()
    runtime = ExecutionRuntime()

    # Pre-register cancel request
    clean_event_bus.request_cancel(run_id)

    with pytest.raises(ExecutionCancelledError):
        runtime.run_graph(graph, memory_mock, dataset_path="test.csv", target="target", run_id=run_id)


# Test 7 — AutoML cancellation
def test_automl_cancellation(clean_event_bus, tmp_path):
    run_id = "run-automl-cancel"
    df = pd.DataFrame({
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "target": [0, 1, 0, 1, 0, 1]
    })

    # Let's request cancellation right after dataset intelligence/model recommendation is completed, 
    # by subscribing to StageCompleted event of "AutoML: Model Recommendation" and issuing request_cancel.
    def on_recommendation(event):
        if event.run_id == run_id and event.payload.get("stage") == "AutoML: Model Recommendation":
            clean_event_bus.request_cancel(run_id)

    clean_event_bus.subscribe("StageCompleted", on_recommendation)

    from mlos.automl.orchestrator import AutoMLOrchestrator
    orchestrator = AutoMLOrchestrator(top_n_models=2, cv_folds=2)

    with pytest.raises(ExecutionCancelledError):
        orchestrator.run_automl(df, target_column="target", output_dir=tmp_path / "automl", run_id=run_id)


# Test 8 — Listener cleanup
def test_listener_cleanup(clean_event_bus, clean_active_runs, tmp_path):
    run_id = "run-listener-cleanup"
    
    # Run the background pipeline inside current thread (to test synchronously)
    # Generate mock project folder
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / ".mlos").mkdir()
    
    # Create sample.csv
    df = pd.DataFrame({
        "f1": [1.0, 2.0, 3.0],
        "target": [0, 1, 0]
    })
    df.to_csv(project_dir / "sample.csv", index=False)
    
    # Initialize active runs state
    with active_runs_lock:
        active_runs[run_id] = {
            "status": "queued",
            "completed_stages": []
        }

    # Verify event bus has normal subscriber count for *
    initial_subscribers = len(clean_event_bus._subscribers.get("*", []))

    background_run_pipeline(run_id, project_dir, "sample.csv", "target")

    # Verify subscription was cleaned up by ensuring no callback named 'on_event' remains
    assert not any(cb.__name__ == "on_event" for cb in clean_event_bus._subscribers.get("*", []))

    # Verify cancellation request was cleared
    assert clean_event_bus.is_cancel_requested(run_id) is False


# Test 9 — Status API
def test_status_api(clean_event_bus, clean_active_runs):
    client = app.test_client()
    run_id = "api-test-run"

    # 1. Start state validation
    response = client.get(f"/api/project/run/status/{run_id}")
    assert response.status_code == 404

    # Populate state
    with active_runs_lock:
        active_runs[run_id] = {
            "status": "running",
            "current_stage": "Transformation",
            "completed_stages": ["Data Loading", "Validation"],
            "error": None
        }

    response = client.get(f"/api/project/run/status/{run_id}")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["status"] == "running"
    assert res_data["current_stage"] == "Transformation"

    # 2. Request cancel
    response = client.post(f"/api/project/run/cancel/{run_id}")
    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["status"] == "cancel_requested"
    assert clean_event_bus.is_cancel_requested(run_id) is True

    # 3. Request cancel on terminal state
    with active_runs_lock:
        active_runs[run_id]["status"] = "completed"

    response = client.post(f"/api/project/run/cancel/{run_id}")
    assert response.status_code == 400
