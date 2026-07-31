"""
Workflow and integration tests for the Reflection subsystem.

Author: Antigravity
License: MIT
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.workflow.workflow_hooks import HookRegistry
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.engine.engine import MLOSEngine
from mlos.domain.models.reflection.reflection_session import ReflectionSession


def test_workflow_engine_triggers_reflection():
    """
    Verify that WorkflowEngine.run() invokes reflect() at the end.
    """
    # 1. Setup mock MLOSEngine
    mlos_engine = MagicMock(spec=MLOSEngine)
    mlos_engine.project_memory = ProjectMemory(
        project_name="TriggerReflect", project_goal="TestGoal"
    )

    # Mock services
    mlos_engine.analyze = MagicMock()
    mlos_engine.planning_service = MagicMock()
    mlos_engine.decision_service = MagicMock()
    mlos_engine.generation_service = MagicMock()
    mlos_engine.assemble = MagicMock()
    mlos_engine.execution_service = MagicMock()
    mlos_engine.evaluation_service = MagicMock()
    mlos_engine.reflection_service = MagicMock()
    mlos_engine.reflect.return_value = MagicMock(spec=ReflectionSession)

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine,
        hooks,
        planning_service=mlos_engine.planning_service,
        decision_service=mlos_engine.decision_service,
        generation_service=mlos_engine.generation_service,
        execution_service=mlos_engine.execution_service,
        evaluation_service=mlos_engine.evaluation_service,
        reflection_service=mlos_engine.reflection_service,
    )

    # Run workflow
    res = workflow.run("dummy_dataset.csv")

    if res.status != "SUCCESS":
        print("WORKFLOW FAILED WITH ERRORS:", res.errors)

    assert res.status == "SUCCESS"
    mlos_engine.reflect.assert_called_once()


def test_regression_detection_and_feedback():
    """
    Construct a history where a metric drops (accuracy: 0.85 -> 0.70)
    and verify that ReflectionService identifies a REGRESSION with high priority feedback.
    """
    engine = MLOSEngine()
    engine.create_project(name="RegressionProj", goal="Identify drop")

    # 1. Populate historical sessions demonstrating a drop in accuracy
    # Setup historical execution success
    t_now = datetime_now_helper()
    exec_session = ExecutionSession(
        pipeline_source=PipelineSource(imports="", body="", code=""),
        status="SUCCESS",
        start_time=t_now,
        end_time=t_now,
        stdout="",
        stderr="",
        exit_code=0,
        duration_seconds=1.0,
    )
    engine.project_memory.execution_sessions.append(exec_session)

    # Setup historical evaluation (high accuracy: 0.85)
    eval_session_1 = EvaluationSession(
        metrics={"accuracy": 0.85},
        checks={"check_1": True},
    )
    engine.project_memory.evaluation_sessions.append(eval_session_1)

    # Setup current evaluation (degraded accuracy: 0.70)
    eval_session_2 = EvaluationSession(
        metrics={"accuracy": 0.70},
        checks={"check_1": True},
    )
    engine.project_memory.evaluation_sessions.append(eval_session_2)

    # 2. Run reflection
    session = engine.reflect()

    # 3. Verify regression detection
    regressions = [i for i in session.insights if i.insight_type == "REGRESSION"]
    assert len(regressions) >= 1
    reg = regressions[0]
    assert reg.severity == "CRITICAL"  # dropped > 10% (from 0.85 to 0.70 is ~17.6%)
    assert "accuracy" in reg.summary

    # 4. Verify feedback generation
    reg_feedback = [f for f in session.feedback if f.target_subsystem == "decision"]
    assert len(reg_feedback) >= 1
    fb = reg_feedback[0]
    assert fb.priority == "HIGH"
    assert fb.action_type == "ADJUST_PARAM"
    assert fb.parameters == {"learning_rate": "decrease", "regularization": "increase"}


def test_backward_compatibility_empty_reflection_sessions():
    """
    Verify that load/reconstruction handles older memories lacking reflection_sessions.
    """
    memory = ProjectMemory(project_name="OldProj", project_goal="OldGoal")

    # Newly initialized project memory should have reflection_sessions as empty list
    assert memory.reflection_sessions == []
    assert memory.reflection_session is None

    # Appending a session via setter works
    mock_session = MagicMock(spec=ReflectionSession)
    memory.reflection_session = mock_session
    assert len(memory.reflection_sessions) == 1
    assert memory.reflection_session == mock_session

    # Setting to None clears the list
    memory.reflection_session = None
    assert memory.reflection_sessions == []
    assert memory.reflection_session is None


def datetime_now_helper():
    from datetime import datetime

    return datetime.now()
