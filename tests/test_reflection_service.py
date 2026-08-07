"""
Integration tests for the ReflectionService.

Author: Antigravity
License: MIT
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.reflection.reflection_session import (
    ReflectionSession as MLOSReflectionSession,
)
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.domain.services.reflection_service import ReflectionService
from mlos.reflection.reflection_engine import ReflectionEngine


def test_build_context_mapping_and_slicing():
    """
    Verify that build_context translates full sessions to summaries and applies window limits.
    """
    # 1. Setup mock engine and memory service
    engine = MagicMock(spec=ReflectionEngine)
    memory_service = MagicMock(spec=ProjectMemoryService)
    service = ReflectionService(engine, memory_service, window_size=3)

    # 2. Setup mock ProjectMemory
    memory = ProjectMemory(
        project_name="DecompositionProj",
        project_goal="Minimizing coupling",
    )

    # Build 5 planning, execution, and evaluation sessions
    for i in range(5):
        # Planning
        plan_context = PlanningContext(project_name="DecompositionProj")
        strategy = ExecutionStrategy(
            strategy_name=f"Strat-{i}", topological_steps=["step1"]
        )
        plan_session = PlanningSession(
            context=plan_context,
            status="SUCCESS",
            selected_execution_strategy=strategy,
        )
        memory.planning_sessions.append(plan_session)

        # Execution
        exec_session = ExecutionSession(
            pipeline_source=PipelineSource(imports="", body="", code=""),
            status="SUCCESS",
            start_time=datetime.now(),
            end_time=datetime.now(),
            stdout="",
            stderr="",
            exit_code=0,
            duration_seconds=1.5,
        )
        memory.execution_sessions.append(exec_session)

        # Evaluation
        eval_session = EvaluationSession(
            metrics={"accuracy": 0.8 + (i * 0.02)},
            checks={"val_check": True},
        )
        memory.evaluation_sessions.append(eval_session)

    # 3. Build context and inspect
    context = service.build_context(memory)

    assert context.project_name == "DecompositionProj"
    assert context.project_goal == "Minimizing coupling"

    # Latest summaries check
    assert context.latest_planning is not None
    assert context.latest_planning.selected_strategy == "Strat-4"
    assert context.latest_execution is not None
    assert context.latest_execution.exit_code == 0
    assert context.latest_evaluation is not None
    assert context.latest_evaluation.metrics["accuracy"] == pytest.approx(0.88)

    # Window slicing check (window_size=3)
    # The historical sequences (excluding latest) has length 4 (indices 0, 1, 2, 3)
    # Slicing with limit=3 should return summaries corresponding to indices 1, 2, 3
    assert len(context.historical_plannings) == 3
    assert context.historical_plannings[0].selected_strategy == "Strat-1"
    assert context.historical_plannings[-1].selected_strategy == "Strat-3"

    assert len(context.historical_executions) == 3
    assert len(context.historical_evaluations) == 3
    assert context.historical_evaluations[0].metrics["accuracy"] == pytest.approx(0.82)


def test_reflect_orchestration_and_persistence():
    """
    Verify that service.reflect invokes the engine and persists the result.
    """
    engine = MagicMock(spec=ReflectionEngine)
    memory_service = MagicMock(spec=ProjectMemoryService)
    service = ReflectionService(engine, memory_service)

    memory = ProjectMemory(project_name="PersistProj", project_goal="TestGoal")

    mock_session = MagicMock(spec=MLOSReflectionSession)
    engine.reflect.return_value = mock_session

    res = service.reflect(memory)

    assert res == mock_session
    engine.reflect.assert_called_once()
    memory_service.add_reflection_session.assert_called_once_with(memory, mock_session)
