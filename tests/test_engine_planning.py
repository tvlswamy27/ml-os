"""
Unit and integration tests for Planning subsystem integration into MLOSEngine and WorkflowEngine.
"""

from unittest.mock import MagicMock

import pytest

from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.planning_service import PlanningService
from mlos.engine.engine import MLOSEngine
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry


def test_mlos_engine_plan_requires_project():
    """
    Ensure MLOSEngine.plan() raises RuntimeError if no project is loaded.
    """
    engine = MLOSEngine()
    assert engine.project_memory is None

    with pytest.raises(RuntimeError) as exc_info:
        engine.plan()
    assert "No project is currently loaded." in str(exc_info.value)


def test_mlos_engine_plan_delegation():
    """
    Verify that MLOSEngine.plan() delegates correctly to PlanningService.plan().
    """
    engine = MLOSEngine()
    memory = ProjectMemory(project_name="TestEngineProj", project_goal="TestGoal")
    engine.project_memory = memory

    # Mock PlanningService
    mock_service = MagicMock(spec=PlanningService)
    mock_session = MagicMock(spec=PlanningSession)
    mock_service.plan.return_value = mock_session
    engine.planning_service = mock_service

    res = engine.plan()
    assert res == mock_session
    mock_service.plan.assert_called_once_with(memory)


def test_workflow_engine_planning_execution_order():
    """
    Verify that WorkflowEngine invokes PlanningService.plan() immediately after analysis
    and before decision.
    """

    class OrderTrackingMLOSEngine:
        def __init__(self):
            self.project_memory = ProjectMemory(
                project_name="OrderProj", project_goal="Test"
            )
            self.execution_engine = MagicMock()
            self.assembly_engine = MagicMock()
            self.decision_engine = MagicMock()
            self.generator_engine = MagicMock()

            self.execution_engine.execute.return_value = MagicMock()
            self.decision_engine.decide.return_value = []
            self.generator_engine.generate.return_value = []

            self.call_order = []

        def analyze(self, path):
            self.call_order.append("analyze")

        def assemble(self, generated_codes=None):
            self.call_order.append("assemble")

        def execute(self):
            self.call_order.append("execute")

        def evaluate(self):
            self.call_order.append("evaluate")

    engine = OrderTrackingMLOSEngine()
    mock_planning_service = MagicMock(spec=PlanningService)

    # When planning runs, record it in call_order
    def plan_mock(mem):
        engine.call_order.append("plan")
        return MagicMock(spec=PlanningSession)

    mock_planning_service.plan.side_effect = plan_mock

    # When decide runs, record it in call_order
    def decide_mock(mem):
        engine.call_order.append("decide")
        return []

    engine.decision_engine.decide.side_effect = decide_mock

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine=engine,
        hooks=hooks,
        planning_service=mock_planning_service,
    )

    res = workflow.run("dummy.csv")
    assert res.status == "SUCCESS"

    # Call order must be: analyze -> plan -> decide
    assert engine.call_order[:3] == ["analyze", "plan", "decide"]


def test_planning_session_appended_to_memory():
    """
    Verify that running engine.plan() successfully appends the resulting PlanningSession to ProjectMemory history.
    """
    engine = MLOSEngine()
    engine.create_project(name="HistoryAppProj", goal="Verify session append")
    assert len(engine.project_memory.planning_sessions) == 0

    session = engine.plan()
    assert isinstance(session, PlanningSession)
    assert len(engine.project_memory.planning_sessions) == 1
    assert engine.project_memory.planning_sessions[0] == session
