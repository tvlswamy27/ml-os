"""
Unit and integration tests for Evaluation subsystem integration.
"""

from datetime import datetime
from unittest.mock import MagicMock
from pathlib import Path
import pytest
import json

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.evaluation_context import EvaluationContext
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.evaluation_result import EvaluationResult
from mlos.evaluation.evaluation_engine import EvaluationEngine
from mlos.domain.services.evaluation_service import EvaluationService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.evaluation.evaluators.simple_evaluator import SimpleEvaluator
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry


def test_evaluation_context_construction():
    """
    Verify EvaluationContext maps ProjectMemory and latest ExecutionSession correctly.
    """
    memory = ProjectMemory(project_name="EvalProj", project_goal="TestGoal")
    source = PipelineSource(imports="", body="", code="")
    session = ExecutionSession(
        pipeline_source=source,
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="run1",
        exit_code=0,
    )
    memory.execution_sessions.append(session)

    service = EvaluationService(
        MagicMock(spec=EvaluationEngine), ProjectMemoryService()
    )
    ctx = service.build_context(memory)
    assert ctx.project_memory == memory
    assert ctx.execution_session == session


def test_evaluation_context_empty_execution_history():
    """
    Verify EvaluationContext maps execution_session to None when history is empty.
    """
    memory = ProjectMemory(project_name="EvalProj", project_goal="TestGoal")
    service = EvaluationService(
        MagicMock(spec=EvaluationEngine), ProjectMemoryService()
    )
    ctx = service.build_context(memory)
    assert ctx.project_memory == memory
    assert ctx.execution_session is None


def test_evaluation_engine_stateless_evaluation(tmp_path):
    """
    Verify EvaluationEngine computes problem-type-specific and general execution metrics.
    """
    memory = ProjectMemory(project_name="EvalProj", project_goal="TestGoal")
    # Setup problem type classification in memory
    from mlos.domain.models.project_profile import ProjectProfile

    memory.project_profile = ProjectProfile(
        problem_type="classification",
        complexity="low",
        baseline_models=[],
        risks=[],
    )

    # Setup execution session and mock metrics file
    project_dir = tmp_path / "playground" / "EvalProj"
    project_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_file = artifacts_dir / "metrics.json"
    metrics_file.write_text(
        json.dumps({"accuracy": 0.85, "r2": 0.99}), encoding="utf-8"
    )  # r2 should be filtered out

    source = PipelineSource(imports="", body="", code="")
    session = ExecutionSession(
        pipeline_source=source,
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="accuracy: 0.85\nloss: 0.12\n",
        exit_code=0,
        duration_seconds=5.5,
        artifacts={"metrics.json": str(metrics_file)},
        metrics_path=str(metrics_file),
    )
    context = EvaluationContext(project_memory=memory, execution_session=session)

    engine = EvaluationEngine()
    engine.register_evaluator(SimpleEvaluator())

    # We patch Path in evaluation_engine module
    import mlos.evaluation.evaluation_engine as ee

    original_path = ee.Path

    class PatchedPath:

        def __new__(cls, *args, **kwargs):
            if args and args[0] == "playground":
                return Path(tmp_path / "playground")
            return Path(*args, **kwargs)

    ee.Path = PatchedPath

    try:
        session_result = engine.evaluate(context)
        assert isinstance(session_result, EvaluationSession)
        assert session_result.status == "SUCCESS"
        assert session_result.metrics["accuracy"] == 0.85
        assert (
            "r2" not in session_result.metrics
        )  # Filtered out since problem type is classification
        assert session_result.metrics["execution_duration"] == 5.5
        assert session_result.metrics["pipeline_success"] == 1.0
        assert session_result.metrics["artifact_generation"] == 1.0
        assert session_result.checks["accuracy_threshold_passed"] is True
    finally:
        ee.Path = original_path


def test_evaluation_engine_empty_session_handling():
    """
    Verify EvaluationEngine gracefully returns status="NO_EXECUTION" on empty execution history.
    """
    memory = ProjectMemory(project_name="EmptyProj", project_goal="TestGoal")
    context = EvaluationContext(project_memory=memory, execution_session=None)
    engine = EvaluationEngine()
    session_result = engine.evaluate(context)
    assert isinstance(session_result, EvaluationSession)
    assert session_result.status == "NO_EXECUTION"
    assert not session_result.metrics
    assert not session_result.checks


def test_evaluation_engine_missing_metrics_file_handling():
    """
    Verify missing metrics file is handled gracefully by falling back to stdout parsing.
    """
    memory = ProjectMemory(project_name="MissingMetricsProj", project_goal="Test")
    session = ExecutionSession(
        pipeline_source=PipelineSource(imports="", body="", code=""),
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="accuracy : 0.92\n",
        exit_code=0,
    )
    context = EvaluationContext(project_memory=memory, execution_session=session)
    engine = EvaluationEngine()
    engine.register_evaluator(SimpleEvaluator())

    session_result = engine.evaluate(context)
    assert session_result.metrics["accuracy"] == 0.92


def test_evaluation_service_orchestration_and_history():
    """
    Verify EvaluationService build/execution/persistence flow.
    """
    memory = ProjectMemory(project_name="TestProj", project_goal="Test")
    session = ExecutionSession(
        pipeline_source=PipelineSource(imports="", body="", code=""),
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="",
        exit_code=0,
    )
    memory.execution_sessions.append(session)

    mock_engine = MagicMock(spec=EvaluationEngine)
    eval_session = EvaluationSession(
        metrics={"accuracy": 0.88}, checks={"ok": True}, status="SUCCESS"
    )
    mock_engine.evaluate.return_value = eval_session

    service = EvaluationService(mock_engine, ProjectMemoryService())
    res = service.evaluate(memory)

    assert res == eval_session
    assert len(memory.evaluation_sessions) == 1
    assert memory.evaluation_sessions[0] == eval_session
    assert memory.evaluation_result.metrics["accuracy"] == 0.88


def test_evaluation_backward_compatibility():
    """
    Verify ProjectMemoryService.update_evaluation_result works backward compatibly by appending EvaluationSession.
    """
    memory = ProjectMemory(project_name="CompatProj", project_goal="Test")
    pm_service = ProjectMemoryService()

    result = EvaluationResult(
        metrics={"accuracy": 0.99},
        checks={"passed": True},
    )

    pm_service.update_evaluation_result(memory, result)
    assert len(memory.evaluation_sessions) == 1
    assert memory.evaluation_sessions[0].metrics["accuracy"] == 0.99
    assert memory.evaluation_result.metrics["accuracy"] == 0.99


def test_workflow_engine_evaluation_ordering():
    """
    Verify WorkflowEngine coordinates Evaluation after Execution.
    """

    class OrderTrackingMLOSEngine:

        def __init__(self):
            self.project_memory = ProjectMemory(
                project_name="WorkflowProj", project_goal="Test"
            )
            self.execution_engine = MagicMock()
            self.decision_engine = MagicMock()
            self.decision_service = MagicMock()
            self.intelligence_engine = MagicMock()

            self.decision_service.decide.return_value = []

            self.call_order = []

        def analyze(self, path):
            self.call_order.append("analyze")

        def assemble(self):
            self.call_order.append("assemble")

        def execute(self):
            self.call_order.append("execute")

        def evaluate(self):
            # Fallback facade
            pass

    engine = OrderTrackingMLOSEngine()

    mock_planning_service = MagicMock()
    mock_planning_service.plan.return_value = MagicMock()

    mock_generation_service = MagicMock()
    mock_generation_service.generate.return_value = []

    mock_execution_service = MagicMock()

    def exec_mock(mem):
        engine.call_order.append("execute")
        return MagicMock()

    mock_execution_service.execute.side_effect = exec_mock

    mock_evaluation_service = MagicMock(spec=EvaluationService)

    def eval_mock(mem):
        engine.call_order.append("evaluate")
        return MagicMock(spec=EvaluationSession)

    mock_evaluation_service.evaluate.side_effect = eval_mock

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine=engine,
        hooks=hooks,
        planning_service=mock_planning_service,
        decision_service=engine.decision_service,
        generation_service=mock_generation_service,
        execution_service=mock_execution_service,
        evaluation_service=mock_evaluation_service,
    )

    res = workflow.run("dummy.csv")
    assert res.status == "SUCCESS"

    # Verify order: analyze -> plan -> decide -> generate -> assemble -> execute -> evaluate
    exc_idx = engine.call_order.index("execute")
    evl_idx = engine.call_order.index("evaluate")
    assert exc_idx < evl_idx
