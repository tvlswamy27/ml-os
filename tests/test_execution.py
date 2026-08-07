"""
Unit tests for the ML-OS Execution Subsystem.
"""

from datetime import datetime
from pathlib import Path

from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.execution_service import ExecutionService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.engine.engine import MLOSEngine
from mlos.execution.execution_engine import ExecutionEngine
from mlos.execution.runners.local_runner import LocalProcessPipelineRunner


def test_domain_models():
    # Verify Pipeline instantiation
    path = Path("/tmp/entry.py")
    pipeline = Pipeline(entrypoint_path=path)
    assert pipeline.entrypoint_path == path
    assert pipeline.configuration_path is None

    # Verify ExecutionResult instantiation
    start = datetime.now()
    result = ExecutionResult(
        status="SUCCESS", start_time=start, stdout="Hello", stderr="Error", exit_code=0
    )
    assert result.status == "SUCCESS"
    assert result.stdout == "Hello"
    assert result.stderr == "Error"
    assert result.exit_code == 0


def test_local_runner_success(tmp_path):
    # Create a success script
    script_path = tmp_path / "success.py"
    script_path.write_text("print('Hello World')\nsys_exit = 0")

    pipeline = Pipeline(entrypoint_path=script_path)
    runner = LocalProcessPipelineRunner()
    result = runner.run(pipeline)

    assert result.status == "SUCCESS"
    assert "Hello World" in result.stdout
    assert result.exit_code == 0
    assert result.end_time is not None
    assert result.end_time >= result.start_time


def test_local_runner_failure(tmp_path):
    # Create a failing script
    script_path = tmp_path / "fail.py"
    script_path.write_text("import sys\nprint('Failing')\nsys.exit(42)")

    pipeline = Pipeline(entrypoint_path=script_path)
    runner = LocalProcessPipelineRunner()
    result = runner.run(pipeline)

    assert result.status == "FAILED"
    assert "Failing" in result.stdout
    assert result.exit_code == 42


def test_execution_engine_delegates():
    class DummyRunner(LocalProcessPipelineRunner):
        def run(self, pipeline):
            return ExecutionResult(
                status="SUCCESS",
                start_time=datetime.now(),
                stdout="dummy stdout",
                exit_code=0,
            )

    pipeline = Pipeline(entrypoint_path=Path("dummy.py"))
    engine = ExecutionEngine(runner=DummyRunner())
    result = engine.execute(pipeline)
    assert result.status == "SUCCESS"
    assert result.stdout == "dummy stdout"


def test_execution_service(tmp_path):
    # Set up memory
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")
    script_path = tmp_path / "run.py"
    script_path.write_text("print('Servicing')")
    memory.pipeline = Pipeline(entrypoint_path=script_path)

    # Set up services
    runner = LocalProcessPipelineRunner()
    engine = ExecutionEngine(runner=runner)
    memory_service = ProjectMemoryService()
    execution_service = ExecutionService(
        execution_engine=engine, project_memory_service=memory_service
    )

    execution_service.run_execution(memory)

    assert memory.execution_result is not None
    assert memory.execution_result.status == "SUCCESS"
    assert "Servicing" in memory.execution_result.stdout


def test_mlos_engine_integration(tmp_path):
    # Setup MLOSEngine
    engine = MLOSEngine()
    engine.create_project(name="IntegrationProj", goal="IntegrationGoal")

    script_path = tmp_path / "integration.py"
    script_path.write_text("print('Integrated')")

    # Manually attach pipeline to memory (since generate is unimplemented)
    engine.project_memory.pipeline = Pipeline(entrypoint_path=script_path)

    engine.execute()

    assert engine.project_memory.execution_result is not None
    assert engine.project_memory.execution_result.status == "SUCCESS"
    assert "Integrated" in engine.project_memory.execution_result.stdout
