"""
PlanningEngine core orchestrator.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm


class PlanningEngine:
    """
    Orchestrator that delegates to an injected PlanningAlgorithm.
    """

    def __init__(self, planning_algorithm: PlanningAlgorithm | None = None):
        """
        Initialize with injected dependency.
        """
        if planning_algorithm is None:
            from mlos.planning.algorithms.heuristic_planning_algorithm import (
                HeuristicPlanningAlgorithm,
            )

            planning_algorithm = HeuristicPlanningAlgorithm()
        self.planning_algorithm = planning_algorithm

    def plan(self, context: PlanningContext) -> PlanningSession:
        """
        Delegate planning to the injected algorithm.
        """
        return self.planning_algorithm.plan(context)
