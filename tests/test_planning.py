"""
Unit tests for the Planning Subsystem Core and Algorithms.
"""

from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.planning.algorithms.heuristic_planning_algorithm import (
    HeuristicPlanningAlgorithm,
)


def test_heuristic_planning_algorithm_defaults():
    algo = HeuristicPlanningAlgorithm()
    context = PlanningContext(project_name="TestProj")
    assert algo.can_plan(context) is True

    session = algo.plan(context)
    assert isinstance(session, PlanningSession)
    assert session.context == context
    assert session.status == "SUCCESS"
    assert not session.observations
    assert not session.hypotheses
    assert not session.candidates
    assert session.selected_execution_strategy is None
