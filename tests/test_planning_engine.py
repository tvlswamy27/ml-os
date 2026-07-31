"""
Unit tests for the PlanningEngine and pluggable algorithms.
"""

from unittest.mock import MagicMock
import pytest

from mlos.planning.planning_engine import PlanningEngine
from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm
from mlos.planning.algorithms.rule_based_algorithm import RuleBasedPlanningAlgorithm
from mlos.planning.algorithms.heuristic_planning_algorithm import (
    HeuristicPlanningAlgorithm,
)
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.observation import Observation
from datetime import datetime


def test_planning_engine_delegation():
    """
    Verify that PlanningEngine delegates the plan call directly to the injected algorithm.
    """
    mock_algo = MagicMock(spec=PlanningAlgorithm)
    context = PlanningContext(project_name="TestProj")
    mock_session = MagicMock(spec=PlanningSession)
    mock_algo.plan.return_value = mock_session

    engine = PlanningEngine(planning_algorithm=mock_algo)
    res = engine.plan(context)

    assert res == mock_session
    mock_algo.plan.assert_called_once_with(context)


def test_planning_engine_stateless():
    """
    Verify that PlanningEngine remains stateless and has no ProjectMemory dependency.
    """
    mock_algo = MagicMock(spec=PlanningAlgorithm)
    engine = PlanningEngine(planning_algorithm=mock_algo)

    # Inspect engine attributes - it should only have its planning_algorithm attribute
    assert len(engine.__dict__) == 1
    assert "planning_algorithm" in engine.__dict__


def test_rule_based_algorithm_can_plan():
    """
    Verify RuleBasedPlanningAlgorithm always can plan.
    """
    algo = RuleBasedPlanningAlgorithm()
    context = PlanningContext(project_name="TestProj")
    assert algo.can_plan(context) is True


def test_rule_based_algorithm_pipeline_success():
    """
    Verify RuleBasedPlanningAlgorithm runs the Template Method reasoning steps and outputs valid objects.
    """
    algo = RuleBasedPlanningAlgorithm()
    observed_at = datetime.now()

    # Context with a missing_values observation to trigger imputation hypothesis
    context = PlanningContext(
        project_name="TestRuleProj",
        observations=(
            Observation(
                source_subsystem="dataset",
                metric_key="missing_values",
                metric_value='{"col1": 5}',
                observed_at=observed_at,
            ),
        ),
    )

    session = algo.plan(context)

    assert isinstance(session, PlanningSession)
    assert session.status == "SUCCESS"
    assert len(session.observations) == 1
    assert session.observations[0].metric_key == "missing_values"

    # Hypotheses
    assert len(session.hypotheses) == 2
    hyp1 = session.hypotheses[0]
    assert "imputing missing values is required" in hyp1.description
    assert hyp1.target_component == "DataImputation"
    assert hyp1.validation_method == "CheckMissingValuesAfterImputation"

    # Candidates
    assert len(session.candidates) == 1
    cand = session.candidates[0]
    assert cand.strategy_name == "RuleBasedPipeline"
    assert cand.steps == ["impute", "scale", "train"]
    assert cand.confidence is not None
    assert cand.confidence.confidence_level == "HIGH"
    assert len(cand.confidence.supporting_evidence) == 2

    # Selected Execution Strategy
    assert session.selected_execution_strategy is not None
    strategy = session.selected_execution_strategy
    assert strategy.strategy_name == "RuleBasedPipeline"
    assert strategy.topological_steps == ["impute", "scale", "train"]
    assert strategy.parameters == {"imputer": "mean", "scaler": "standard"}


def test_heuristic_algorithm_conformance():
    """
    Verify HeuristicPlanningAlgorithm runs successfully under the Template Method pattern.
    """
    algo = HeuristicPlanningAlgorithm()
    context = PlanningContext(project_name="HeuristicProj")

    session = algo.plan(context)

    assert isinstance(session, PlanningSession)
    assert session.status == "SUCCESS"
    assert len(session.observations) == 0
    assert len(session.hypotheses) == 0
    assert len(session.candidates) == 0
    assert session.selected_execution_strategy is None
