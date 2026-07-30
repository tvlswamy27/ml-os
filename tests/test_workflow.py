"""
Unit and integration tests for the ML-OS Workflow Engine.
"""

from pathlib import Path
from datetime import datetime
import pytest

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.workflow_result import WorkflowResult
from mlos.workflow.workflow_hooks import HookRegistry, WorkflowHook
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.engine.engine import MLOSEngine


def test_workflow_result_instantiation():
    start = datetime.now()
    res = WorkflowResult(status="SUCCESS", start_time=start, end_time=datetime.now())
    assert res.status == "SUCCESS"
    assert res.start_time == start
    assert not res.errors


def test_hook_registry():
    registry = HookRegistry()
    triggered = []

    def callback(arg):
        triggered.append(arg)

    registry.subscribe(WorkflowHook.BEFORE_ANALYSIS, callback)
    registry.trigger(WorkflowHook.BEFORE_ANALYSIS, "test_data")

    assert triggered == ["test_data"]


def test_workflow_engine_error_capture():
    # Setup a mock MLOSEngine that fails during analyze()
    class BrokenMLOSEngine:
        def __init__(self):
            self.project_memory = ProjectMemory(project_name="Broken", project_goal="Fail")

        def analyze(self, path):
            raise ValueError("Invalid dataset format")

    hooks = HookRegistry()
    engine = BrokenMLOSEngine()
    workflow = WorkflowEngine(engine, hooks)

    res = workflow.run("dummy.csv")
    assert res.status == "FAILED"
    assert "ValueError" in res.errors["lifecycle_run"]
    assert "Invalid dataset format" in res.errors["lifecycle_run"]


def test_workflow_engine_hooks_execution(tmp_path):
    # Setup MLOSEngine
    mlos_engine = MLOSEngine()
    mlos_engine.create_project(name="HookProj", goal="Verify hooks trigger")

    # Set up triggers list
    hooks_triggered = []

    def before_analysis_cb(dataset_path):
        hooks_triggered.append(("before_analysis", dataset_path))

    def after_analysis_cb(memory):
        hooks_triggered.append(("after_analysis", memory.project_name))

    def before_execution_cb(memory):
        hooks_triggered.append(("before_execution", memory.project_name))

    def after_execution_cb(memory):
        hooks_triggered.append(("after_execution", memory.project_name))

    mlos_engine.hooks.subscribe(WorkflowHook.BEFORE_ANALYSIS, before_analysis_cb)
    mlos_engine.hooks.subscribe(WorkflowHook.AFTER_ANALYSIS, after_analysis_cb)
    mlos_engine.hooks.subscribe(WorkflowHook.BEFORE_EXECUTION, before_execution_cb)
    mlos_engine.hooks.subscribe(WorkflowHook.AFTER_EXECUTION, after_execution_cb)

    # Mock the rest of execution flow to prevent disk writes/subprocess launches in this test
    # By replacing MLOSEngine execute/evaluate methods temporarily
    original_execute = mlos_engine.execute
    original_evaluate = mlos_engine.evaluate
    original_assemble = mlos_engine.assemble

    mlos_engine.execute = lambda: hooks_triggered.append(("executed", True))
    mlos_engine.evaluate = lambda: hooks_triggered.append(("evaluated", True))
    mlos_engine.assemble = lambda codes: hooks_triggered.append(("assembled", len(codes)))

    # Run the workflow
    res = mlos_engine.run("playground/sample.csv")

    assert res.status == "SUCCESS"
    assert ("before_analysis", "playground/sample.csv") in hooks_triggered
    assert ("after_analysis", "HookProj") in hooks_triggered
    assert ("before_execution", "HookProj") in hooks_triggered
    assert ("executed", True) in hooks_triggered
    assert ("after_execution", "HookProj") in hooks_triggered
    assert ("evaluated", True) in hooks_triggered

    # Clean up project dir
    project_dir = Path("playground") / "HookProj"
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)


def test_full_mlos_engine_run_integration(tmp_path):
    # Setup MLOSEngine
    engine = MLOSEngine()
    engine.create_project(name="FullWorkflowProj", goal="Complete run validation")

    # In ML-OS, DecisionEngine uses dataset metrics to select strategies.
    # Since GeneratorEngine currently only supports MissingValue decisions, running on playground/sample.csv
    # will trigger MissingValue decisions and generate imputation code.
    # The pipeline.py will execute and finish successfully.
    
    # Run the workflow end-to-end
    result = engine.run("playground/sample.csv")

    # Verify run completed successfully
    assert result.status == "SUCCESS"
    assert engine.project_memory.pipeline is not None
    assert engine.project_memory.execution_result is not None
    assert engine.project_memory.execution_result.status == "SUCCESS"
    assert engine.project_memory.evaluation_result is not None

    # Verify simple evaluator output metrics parsed (from stdout fallback in v1)
    # The generated script is run in sys.executable. Let's make sure it contains code and was executed.
    # In v1, execution result captures stdout which we check here:
    assert engine.project_memory.execution_result.exit_code == 0
    assert "SimpleImputer" in engine.project_memory.pipeline.entrypoint_path.read_text()

    # Clean up
    project_dir = Path("playground") / "FullWorkflowProj"
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)
