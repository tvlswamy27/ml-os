"""
Unit tests for the PlanningService class.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from mlos.domain.models.dataset import Dataset
from mlos.domain.models.evaluation_result import EvaluationResult
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.planning.observation import Observation
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile
from mlos.domain.models.risk import Risk
from mlos.domain.services.planning_service import PlanningService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.planning.planning_engine import PlanningEngine


def test_planning_service_dependency_injection():
    """
    Verify PlanningService correctly receives and holds injected dependencies.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = MagicMock(spec=ProjectMemoryService)

    service = PlanningService(
        planning_engine=mock_engine,
        project_memory_service=mock_mem_service,
    )

    assert service.planning_engine == mock_engine
    assert service.project_memory_service == mock_mem_service


def test_build_context_empty_memory():
    """
    Verify build_context behaves correctly with a minimal ProjectMemory containing no optional profiles.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = MagicMock(spec=ProjectMemoryService)

    memory = ProjectMemory(
        project_name="EmptyProj",
        project_goal="Solve cold start",
    )

    service = PlanningService(mock_engine, mock_mem_service)
    context = service.build_context(memory)

    assert isinstance(context, PlanningContext)
    assert context.project_name == "EmptyProj"
    assert len(context.goals) == 1
    assert context.goals[0].name == "project_goal"
    assert context.goals[0].target_value == "Solve cold start"
    assert isinstance(context.goals, tuple)
    assert isinstance(context.observations, tuple)
    assert isinstance(context.constraints, tuple)
    assert isinstance(context.assumptions, tuple)
    assert len(context.constraints) == 0
    assert len(context.assumptions) == 0

    # Optional fields absent: only current_stage is mapped as default observation
    assert len(context.observations) == 1
    assert context.observations[0].source_subsystem == "current_stage"


def test_build_context_missing_optional_fields():
    """
    Ensure build_context never fails when optional fields (dataset, profile, etc.) are partially set or missing.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = MagicMock(spec=ProjectMemoryService)

    memory = ProjectMemory(
        project_name="PartialProj",
        project_goal="Optimize latency",
    )
    # Provide dataset but no project_profile, execution_result, or evaluation_result
    memory.dataset = Dataset(path="data.csv", rows=100, columns=5)
    memory.notes = ["Need feature scaling"]

    service = PlanningService(mock_engine, mock_mem_service)
    context = service.build_context(memory)

    assert context.project_name == "PartialProj"
    # Goals: project_goal
    assert len(context.goals) == 1
    # Observations: current_stage, notes, dataset path, rows, columns, duplicate_rows
    assert len(context.observations) > 3

    sources = {obs.source_subsystem for obs in context.observations}
    assert "current_stage" in sources
    assert "notes" in sources
    assert "dataset" in sources
    assert "project_profile" not in sources
    assert "execution_result" not in sources
    assert "evaluation_result" not in sources


def test_build_context_fully_mapped():
    """
    Verify that a fully populated ProjectMemory is mapped accurately to a PlanningContext.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = MagicMock(spec=ProjectMemoryService)

    memory = ProjectMemory(
        project_name="CompleteProj",
        project_goal="Maximize score",
    )
    memory.current_stage = "Evaluating"
    memory.completed_tasks = ["Preprocessing", "Training"]
    memory.notes = ["First try", "Good enough"]

    memory.dataset = Dataset(
        path="train.csv",
        rows=500,
        columns=10,
        target="label",
        problem_type="classification",
        categorical_columns=["c1"],
        numerical_columns=["n1"],
        missing_values={"c1": 2},
        duplicate_rows=1,
        unique_values={"label": 2},
        missing_percentages={"c1": 0.4},
        column_types={"c1": "object"},
    )

    memory.project_profile = ProjectProfile(
        problem_type="classification",
        complexity="low",
        baseline_models=["LogisticRegression"],
        risks=[Risk(title="Overfitting", severity="high", description="risky")],
    )

    memory.pipeline = Pipeline(
        entrypoint_path=Path("run.py"),
        configuration_path=Path("config.yaml"),
    )

    memory.execution_result = ExecutionResult(
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="done",
        stderr="",
        exit_code=0,
    )

    memory.evaluation_result = EvaluationResult(
        metrics={"accuracy": 0.92},
        checks={"accuracy_check": True},
    )

    service = PlanningService(mock_engine, mock_mem_service)
    context = service.build_context(memory)

    assert context.project_name == "CompleteProj"
    assert isinstance(context.goals, tuple)
    assert isinstance(context.observations, tuple)

    # Convert observations to dictionary key mapping for ease of testing
    obs_map = {
        (obs.source_subsystem, obs.metric_key): obs.metric_value
        for obs in context.observations
    }

    # Verify stage & task & notes
    assert obs_map[("current_stage", "stage")] == "Evaluating"
    assert obs_map[("completed_tasks", "tasks")] == "Preprocessing,Training"
    assert obs_map[("notes", "note_0")] == "First try"
    assert obs_map[("notes", "note_1")] == "Good enough"

    # Verify dataset
    assert obs_map[("dataset", "path")] == "train.csv"
    assert obs_map[("dataset", "rows")] == "500"
    assert obs_map[("dataset", "columns")] == "10"
    assert obs_map[("dataset", "target")] == "label"
    assert obs_map[("dataset", "problem_type")] == "classification"
    assert obs_map[("dataset", "categorical_columns")] == "c1"
    assert obs_map[("dataset", "numerical_columns")] == "n1"
    import json

    assert json.loads(obs_map[("dataset", "missing_values")]) == {"c1": 2}
    assert obs_map[("dataset", "duplicate_rows")] == "1"

    # Verify project profile
    assert obs_map[("project_profile", "problem_type")] == "classification"
    assert obs_map[("project_profile", "complexity")] == "low"
    assert obs_map[("project_profile", "baseline_models")] == "LogisticRegression"
    assert "risk:Overfitting" in [k[1] for k in obs_map if k[0] == "project_profile"]

    # Verify pipeline
    assert obs_map[("pipeline", "entrypoint_path")] == "run.py"
    assert obs_map[("pipeline", "configuration_path")] == "config.yaml"

    # Verify execution result
    assert obs_map[("execution_result", "status")] == "SUCCESS"
    assert obs_map[("execution_result", "exit_code")] == "0"
    assert obs_map[("execution_result", "stdout")] == "done"

    # Verify evaluation result
    assert obs_map[("evaluation_result", "metric:accuracy")] == "0.92"
    assert obs_map[("evaluation_result", "check:accuracy_check")] == "True"


def test_stateless_run_planning():
    """
    Verify run_planning only depends on PlanningContext and executes the engine statelessly.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = MagicMock(spec=ProjectMemoryService)

    context = PlanningContext(project_name="StatelessProj")
    mock_session = MagicMock(spec=PlanningSession)
    mock_engine.plan.return_value = mock_session

    service = PlanningService(mock_engine, mock_mem_service)
    session = service.run_planning(context)

    assert session == mock_session
    mock_engine.plan.assert_called_once_with(context)
    # Assert ProjectMemoryService was not accessed
    mock_mem_service.add_planning_session.assert_not_called()


def test_plan_orchestration():
    """
    Verify plan() coordinates the end-to-end building, stateless execution, and persistence flow.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = (
        ProjectMemoryService()
    )  # Use actual service to check mutability side effect

    memory = ProjectMemory(
        project_name="OrchestrateProj",
        project_goal="End to end test",
    )

    mock_session = MagicMock(spec=PlanningSession)
    mock_engine.plan.return_value = mock_session

    service = PlanningService(mock_engine, mock_mem_service)
    session = service.plan(memory)

    assert session == mock_session
    assert len(memory.planning_sessions) == 1
    assert memory.planning_sessions[0] == mock_session


def test_planning_history_isolation():
    """
    Ensure previous PlanningSessions inside ProjectMemory.planning_sessions are NOT replayed
    or automatically aggregated into subsequent build_context calls.
    """
    mock_engine = MagicMock(spec=PlanningEngine)
    mock_mem_service = ProjectMemoryService()

    memory = ProjectMemory(
        project_name="HistoryProj",
        project_goal="Verify isolation",
    )

    # 1. First planning session
    session1 = PlanningSession(
        context=PlanningContext(project_name="HistoryProj"),
        status="SUCCESS",
        observations=[
            Observation(
                source_subsystem="test",
                metric_key="k1",
                metric_value="v1",
                observed_at=datetime.now(),
            )
        ],
    )

    mock_engine.plan.return_value = session1

    service = PlanningService(mock_engine, mock_mem_service)

    # Executing first plan adds session1 to history
    res1 = service.plan(memory)
    assert res1 == session1
    assert len(memory.planning_sessions) == 1

    # 2. Build context for second planning session
    context2 = service.build_context(memory)

    # Verify that the observation "k1" from session1's observations list was NOT copied to context2
    assert not any(obs.metric_key == "k1" for obs in context2.observations)
