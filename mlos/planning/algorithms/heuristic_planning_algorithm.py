from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.reasoning_state import ReasoningState


class HeuristicPlanningAlgorithm(PlanningAlgorithm):
    """
    A bootstrapping planning algorithm that returns an empty planning session.
    """

    def can_plan(self, context: PlanningContext) -> bool:
        """
        Always returns True to serve as a baseline fallback planner.
        """
        return True

    def _analyze_observations(self, context: PlanningContext) -> ReasoningState:
        return ReasoningState(facts={})

    def _generate_hypotheses(self, reasoning_state: ReasoningState) -> list[Hypothesis]:
        return []

    def _generate_candidate_strategies(
        self, hypotheses: list[Hypothesis]
    ) -> list[CandidateStrategy]:
        return []

    def _evaluate_candidate_strategies(
        self, candidates: list[CandidateStrategy], hypotheses: list[Hypothesis]
    ) -> dict[str, float]:
        return {}

    def _enrich_candidates(
        self,
        candidates: list[CandidateStrategy],
        reasoning_state: ReasoningState,
        hypotheses: list[Hypothesis],
    ) -> list[CandidateStrategy]:
        return []

    def _select_final_strategy(
        self, candidates: list[CandidateStrategy], scores: dict[str, float]
    ) -> ExecutionStrategy | None:
        return None

    def _construct_session(
        self,
        context: PlanningContext,
        hypotheses: list[Hypothesis],
        candidates: list[CandidateStrategy],
        selected: ExecutionStrategy | None,
    ) -> PlanningSession:
        return PlanningSession(
            context=context,
            status="SUCCESS",
            observations=[],
            hypotheses=[],
            candidates=[],
            selected_execution_strategy=None,
        )
