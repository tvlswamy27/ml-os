"""
Unit and integration tests for Execution subsystem integration.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from mlos.domain.models.execution_context import ExecutionContext
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.execution_service import ExecutionService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.execution.execution_engine import ExecutionEngine
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry


def test_execution_context_construction():
    """
    Verify ExecutionContext maps ProjectMemory and PipelineSource correctly.
    """
    memory = ProjectMemory(project_name="ExecProj", project_goal="TestGoal")
    source = PipelineSource(
        imports="import sys", body="print('ok')", code="import sys\nprint('ok')"
    )
    memory.pipeline_source = source

    service = ExecutionService(MagicMock(spec=ExecutionEngine), ProjectMemoryService())
    ctx = service.build_context(memory)
    assert ctx.project_memory == memory
    assert ctx.pipeline_source == source


def test_execution_engine_execute_session_creation(tmp_path):
    """
    Verify ExecutionEngine runs runner, calculates timing/hash, and constructs ExecutionSession.
    """
    memory = ProjectMemory(project_name="ExecProj", project_goal="TestGoal")
    # Setup mock pipeline
    script_path = tmp_path / "pipeline.py"
    script_path.write_text("print('Executing')", encoding="utf-8")
    pipeline = Pipeline(entrypoint_path=script_path.resolve())
    memory.pipeline = pipeline

    source = PipelineSource(imports="", body="", code="print('Executing')")
    context = ExecutionContext(project_memory=memory, pipeline_source=source)

    # Setup mock runner
    mock_runner = MagicMock()
    mock_runner.run.return_value = ExecutionResult(
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="Executing\n",
        stderr="",
        exit_code=0,
    )

    engine = ExecutionEngine(mock_runner)
    session = engine.execute(context)

    assert isinstance(session, ExecutionSession)
    assert session.status == "SUCCESS"
    assert session.stdout == "Executing\n"
    assert session.exit_code == 0
    assert session.pipeline_hash is not None
    assert len(session.pipeline_hash) == 64  # sha256 hex length
    assert session.duration_seconds >= 0.0


def test_execution_service_orchestration_and_history():
    """
    Verify ExecutionService orchestration and chronological execution_sessions appending.
    """
    memory = ProjectMemory(project_name="ExecProj", project_goal="TestGoal")
    # Pre-populate pipeline and pipeline_source
    memory.pipeline = Pipeline(entrypoint_path=Path("dummy_path"))
    source = PipelineSource(imports="", body="", code="pass")
    memory.pipeline_source = source

    mock_engine = MagicMock(spec=ExecutionEngine)
    session1 = ExecutionSession(
        pipeline_source=source,
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="run1",
        exit_code=0,
    )
    session2 = ExecutionSession(
        pipeline_source=source,
        status="FAILED",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="run2",
        exit_code=1,
    )

    mock_engine.execute.side_effect = [session1, session2]

    service = ExecutionService(mock_engine, ProjectMemoryService())

    # Run execution 1
    res1 = service.execute(memory)
    assert res1 == session1
    assert len(memory.execution_sessions) == 1
    assert memory.execution_sessions[0] == session1
    # Check backward compatibility property
    assert memory.execution_result.status == "SUCCESS"
    assert memory.execution_result.stdout == "run1"

    # Run execution 2 (appends to history)
    res2 = service.execute(memory)
    assert res2 == session2
    assert len(memory.execution_sessions) == 2
    assert memory.execution_sessions[0] == session1
    assert memory.execution_sessions[1] == session2
    # Check backward compatibility property reflects the latest session
    assert memory.execution_result.status == "FAILED"
    assert memory.execution_result.stdout == "run2"


def test_project_memory_service_backward_compatibility():
    """
    Verify ProjectMemoryService.update_execution_result works backward compatibly by appending ExecutionSession.
    """
    memory = ProjectMemory(project_name="CompatProj", project_goal="Test")
    pm_service = ProjectMemoryService()

    result = ExecutionResult(
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
        stdout="compat output",
        exit_code=0,
    )

    pm_service.update_execution_result(memory, result)
    assert len(memory.execution_sessions) == 1
    assert memory.execution_sessions[0].stdout == "compat output"
    assert memory.execution_result.stdout == "compat output"


def test_workflow_engine_execution_ordering():
    """
    Verify WorkflowEngine coordinates Execution after Assembly.
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
            # Fallback facade
            pass

        def evaluate(self):
            self.call_order.append("evaluate")

    engine = OrderTrackingMLOSEngine()

    mock_planning_service = MagicMock()
    mock_planning_service.plan.return_value = MagicMock()

    mock_generation_service = MagicMock()
    mock_generation_service.generate.return_value = []

    mock_execution_service = MagicMock(spec=ExecutionService)

    def exec_mock(mem):
        engine.call_order.append("execute")
        return MagicMock(spec=ExecutionSession)

    mock_execution_service.execute.side_effect = exec_mock

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine=engine,
        hooks=hooks,
        planning_service=mock_planning_service,
        decision_service=engine.decision_service,
        generation_service=mock_generation_service,
        execution_service=mock_execution_service,
    )

    res = workflow.run("dummy.csv")
    assert res.status == "SUCCESS"

    # Verify order: analyze -> plan -> decide -> generate -> assemble -> execute
    asm_idx = engine.call_order.index("assemble")
    exc_idx = engine.call_order.index("execute")
    assert asm_idx < exc_idx
