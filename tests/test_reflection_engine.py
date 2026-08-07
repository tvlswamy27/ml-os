"""
Unit tests for the ReflectionEngine and RuleBasedReflectionAlgorithm.

Author: Antigravity
License: MIT
"""

from unittest.mock import MagicMock

from mlos.domain.models.reflection.reflection_context import (
    EvaluationSummary,
    ExecutionSummary,
    ReflectionContext,
)
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.reflection.algorithms.reflection_algorithm import ReflectionAlgorithm
from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
    RuleBasedReflectionAlgorithm,
)
from mlos.reflection.reflection_engine import ReflectionEngine


def test_reflection_engine_delegation():
    """
    Verify that ReflectionEngine delegates directly to the injected algorithm.
    """
    mock_algo = MagicMock(spec=ReflectionAlgorithm)
    context = ReflectionContext(
        project_name="TestProj",
        project_goal="TestGoal",
        latest_planning=None,
        latest_execution=None,
        latest_evaluation=None,
    )
    mock_session = MagicMock(spec=ReflectionSession)
    mock_algo.reflect.return_value = mock_session

    engine = ReflectionEngine(reflection_algorithm=mock_algo)
    res = engine.reflect(context)

    assert res == mock_session
    mock_algo.reflect.assert_called_once_with(context)


def test_reflection_engine_stateless():
    """
    Verify that ReflectionEngine is stateless and holds no dynamic workspace variables.
    """
    mock_algo = MagicMock(spec=ReflectionAlgorithm)
    engine = ReflectionEngine(reflection_algorithm=mock_algo)

    assert len(engine.__dict__) == 1
    assert "reflection_algorithm" in engine.__dict__


def test_rule_based_algorithm_can_reflect():
    """
    Verify RuleBasedReflectionAlgorithm can reflect by default.
    """
    algo = RuleBasedReflectionAlgorithm()
    context = ReflectionContext(
        project_name="TestProj",
        project_goal="TestGoal",
        latest_planning=None,
        latest_execution=None,
        latest_evaluation=None,
    )
    assert algo.can_reflect(context) is True


def test_rule_based_algorithm_empty_history():
    """
    Verify RuleBasedReflectionAlgorithm handles empty history gracefully and generates baseline recommendations.
    """
    algo = RuleBasedReflectionAlgorithm()
    context = ReflectionContext(
        project_name="TestProj",
        project_goal="TestGoal",
        latest_planning=None,
        latest_execution=None,
        latest_evaluation=None,
    )

    session = algo.reflect(context)
    assert isinstance(session, ReflectionSession)
    assert any("initialized" in ins.summary.lower() for ins in session.insights)
    assert len(session.insights) == 1
    assert session.insights[0].insight_type == "METRIC_TREND"

    assert len(session.feedback) == 1
    fb = session.feedback[0]
    assert fb.target_subsystem == "planning"
    assert fb.action_type == "ENABLE_IMPUTATION"
    assert fb.priority == "CRITICAL"
    assert fb.parameters == {"pipeline_type": "baseline"}
    assert session.confidence is not None
    assert session.confidence.accepted is False  # Low history, low confidence


def test_rule_based_algorithm_confidence_acceptance():
    """
    Verify that ReflectionConfidence has 'accepted' computed properly.
    """
    algo = RuleBasedReflectionAlgorithm()

    # 1. Mock context with long history of high metrics to trigger high confidence
    hist_evals = tuple(
        EvaluationSummary(session_id=f"EVAL-{i}", metrics={"accuracy": 0.85})
        for i in range(10)
    )
    hist_execs = tuple(
        ExecutionSummary(
            session_id=f"EXEC-{i}",
            status="SUCCESS",
            exit_code=0,
            duration_seconds=1.0,
            error_message=None,
        )
        for i in range(10)
    )
    context = ReflectionContext(
        project_name="TestProj",
        project_goal="TestGoal",
        latest_planning=None,
        latest_execution=ExecutionSummary("EXEC-L", "SUCCESS", 0, 1.0, None),
        latest_evaluation=EvaluationSummary("EVAL-L", {"accuracy": 0.85}),
        historical_evaluations=hist_evals,
        historical_executions=hist_execs,
    )

    session = algo.reflect(context)
    assert session.confidence is not None
    assert session.confidence.score >= 0.7
    assert session.confidence.uncertainty <= 0.3
    assert session.confidence.accepted is True
