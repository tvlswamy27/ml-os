"""
Unit and integration tests for ML-OS v3.0 core features.

Author: Antigravity
License: MIT
"""

import pytest
import shutil
import tempfile
import json
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

from mlos.sdk.project import MLProject
from mlos.registry.artifact_registry import ArtifactRegistry, ExecutionArtifact
from mlos.experiment.models import Experiment, Run
from mlos.experiment.tracker import ExperimentTracker
from mlos.communication.event_bus import GlobalEventBus
from mlos.communication.store import EventStore
from mlos.adaptive_planning.planner import (
    AdaptivePlanner,
    ExecutionDiff,
    ExecutionMutation,
)
from mlos.domain.models.meta_reasoning.execution_schedule import (
    ExecutionSchedule,
    ScheduleNode,
    ScheduleDependency,
)
from mlos.domain.enums.subsystem_name import SubsystemName


@pytest.fixture
def temp_project_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_artifact_registry(temp_project_dir):
    registry = ArtifactRegistry(str(temp_project_dir))

    # Create a dummy source file
    dummy_src = temp_project_dir / "test_model.pkl"
    with open(dummy_src, "w") as f:
        f.write("dummy model content")

    # Register artifact
    art = registry.register_artifact(
        name="test_rf_model",
        artifact_type="MODEL",
        source_file_path=dummy_src,
        version="1.2.0",
        metadata={"accuracy": 0.95},
    )

    assert art.name == "test_rf_model"
    assert art.artifact_type == "MODEL"
    assert art.version == "1.2.0"
    assert art.metadata["accuracy"] == 0.95
    assert (temp_project_dir / art.file_path).exists()
    assert "artifacts/models/test_model.pkl" in art.file_path.replace("\\", "/")

    # Retrieve
    retrieved = registry.get_artifact(art.artifact_id)
    assert retrieved is not None
    assert retrieved.name == "test_rf_model"

    # List filtering
    models_list = registry.list_artifacts(artifact_type="MODEL")
    assert len(models_list) == 1

    reports_list = registry.list_artifacts(artifact_type="REPORT")
    assert len(reports_list) == 0


def test_experiment_tracker(temp_project_dir):
    tracker = ExperimentTracker(str(temp_project_dir))

    # Get or create
    exp = tracker.get_or_create_experiment("TabularClassifiers")
    assert exp.name == "TabularClassifiers"
    assert len(exp.runs) == 0

    # Create fake execution, metrics, snapshots to build a Run
    from mlos.experiment.models import (
        RunExecution,
        RunMetrics,
        RunArtifact,
        RunEvent,
        KnowledgeSnapshot,
    )

    execution = RunExecution(
        execution_id=uuid4(),
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=5.2,
        stdout="Trained RandomForest",
        stderr="",
        exit_code=0,
    )
    metrics = RunMetrics(uuid4(), {"accuracy": 0.89}, datetime.now())
    snapshot = KnowledgeSnapshot(uuid4(), datetime.now(), 0, [])

    run = Run(
        run_id=uuid4(),
        experiment_id=exp.experiment_id,
        name="run_1",
        timestamp=datetime.now(),
        execution=execution,
        metrics=metrics,
        artifacts=[],
        events=[],
        knowledge_snapshot=snapshot,
    )

    tracker.record_run(exp.experiment_id, run)

    # Reload and assert
    tracker2 = ExperimentTracker(str(temp_project_dir))
    exp_loaded = tracker2.get_or_create_experiment("TabularClassifiers")
    assert len(exp_loaded.runs) == 1
    assert exp_loaded.runs[0].name == "run_1"
    assert exp_loaded.runs[0].metrics.metrics["accuracy"] == 0.89


def test_global_event_bus_and_store(temp_project_dir):
    bus = GlobalEventBus()
    bus.clear()
    store = EventStore(str(temp_project_dir))

    captured_events = []

    def callback(event):
        captured_events.append(event)

    bus.subscribe("TestEvent", callback)

    # Publish
    ev = bus.publish(event_type="TestEvent", source="UnitTest", payload={"val": 42})

    assert len(captured_events) == 1
    assert captured_events[0].event_type == "TestEvent"
    assert captured_events[0].payload["val"] == 42

    # Verify persistence inside EventStore
    assert len(store.get_timeline()) == 1
    assert store.get_timeline()[0].event_type == "TestEvent"
    assert store.get_timeline()[0].source == "UnitTest"

    # Replay
    replayed = store.replay()
    assert len(replayed) == 1
    assert replayed[0].event_id == ev.event_id

    # Shutdown store subscription
    store.shutdown()


def test_adaptive_planner_cycles():
    planner = AdaptivePlanner()

    # Build schedule with no cycle
    node_a = ScheduleNode("node_a", SubsystemName.PLANNING, "ALWAYS", False)
    node_b = ScheduleNode("node_b", SubsystemName.EXECUTION, "ALWAYS", False)
    dep = ScheduleDependency("node_a", "node_b", "SEQUENTIAL")

    schedule = ExecutionSchedule((node_a, node_b), (dep,), 1)

    # Replace B
    diff = ExecutionDiff(
        [ExecutionMutation("REPLACE", "node_b", SubsystemName.EVALUATION)]
    )
    patched = planner.apply_diff(schedule, diff)
    assert len(patched.nodes) == 2
    assert patched.nodes[1].subsystem == SubsystemName.EVALUATION

    # Introduce a cyclic mutation (ADD node_c depending on node_b, and make node_a depend on node_c)
    # A -> B -> C -> A
    diff_cycle = ExecutionDiff(
        [
            ExecutionMutation(
                "ADD", "node_c", SubsystemName.PLANNING, dependencies=["node_b"]
            ),
            ExecutionMutation(
                "ADD", "node_a", SubsystemName.PLANNING, dependencies=["node_c"]
            ),
        ]
    )
    with pytest.raises(ValueError, match="dependency cycle"):
        planner.apply_diff(patched, diff_cycle)


def test_ml_project_e2e(temp_project_dir):
    # Setup dummy dataset file
    dataset_path = temp_project_dir / "sample.csv"
    with open(dataset_path, "w") as f:
        f.write("feature_1,feature_2,label\n1,2,0\n3,4,1\n5,6,0\n7,8,1\n")

    project = MLProject(
        dataset_path=str(dataset_path),
        target_column="label",
        project_path=str(temp_project_dir),
        name="IntegrationProject",
        goal="Verify E2E Framework",
    )

    # Execute full stage-based execution run
    session = project.run()

    # Check session
    report = session.get_evaluation_report()
    assert report["status"] == "SUCCESS"
    assert "metrics" in report

    # Check SDK helper APIs
    metrics = project.metrics()
    assert isinstance(metrics, dict)
    assert len(metrics) > 0

    artifacts = project.artifacts()
    assert len(artifacts) > 0
    types = [a.artifact_type for a in artifacts]
    assert "MODEL" in types
    assert "DEPLOYMENT" in types

    graph = project.graph()
    assert len(graph["nodes"]) == 10

    history = project.history()
    assert len(history) == 1
    assert history[0]["name"] == "run_1"

    comparison = project.compare_runs()
    assert "run_1" in comparison

    # Test project save/load transparency
    project.save()

    loaded_project = MLProject.load(str(temp_project_dir))
    assert loaded_project.name == "IntegrationProject"
    assert loaded_project.goal == "Verify E2E Framework"
    assert loaded_project.target_column == "label"

    # Export zip
    zip_path = temp_project_dir / "export.zip"
    exported = project.export(str(zip_path))
    assert Path(exported).exists()
