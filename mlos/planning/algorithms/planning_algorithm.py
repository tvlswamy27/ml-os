"""
PlanningAlgorithm interface.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.reasoning_state import ReasoningState


class PlanningAlgorithm(ABC):
    """
    Abstract Base Class defining the interface for all planning algorithms.
    """

    @abstractmethod
    def can_plan(self, context: PlanningContext) -> bool:
        """
        Check if the algorithm supports the given planning context.

        Args:
            context: The planning context representing goals, constraints, and observations.

        Returns:
            bool: True if this algorithm can generate a plan for the context, False otherwise.
        """
        pass

    def plan(self, context: PlanningContext) -> PlanningSession:
        """
        Template Method: Orchestrates the execution of the 7 protected planning phases.
        """
        reasoning_state = self._analyze_observations(context)
        hypotheses = self._generate_hypotheses(reasoning_state)
        candidates = self._generate_candidate_strategies(hypotheses)
        scores = self._evaluate_candidate_strategies(candidates, hypotheses)
        enriched_candidates = self._enrich_candidates(
            candidates, reasoning_state, hypotheses
        )
        selected_strategy = self._select_final_strategy(enriched_candidates, scores)
        return self._construct_session(
            context, hypotheses, enriched_candidates, selected_strategy
        )

    @abstractmethod
    def _analyze_observations(self, context: PlanningContext) -> ReasoningState:
        pass

    @abstractmethod
    def _generate_hypotheses(self, reasoning_state: ReasoningState) -> list[Hypothesis]:
        pass

    @abstractmethod
    def _generate_candidate_strategies(
        self, hypotheses: list[Hypothesis]
    ) -> list[CandidateStrategy]:
        pass

    @abstractmethod
    def _evaluate_candidate_strategies(
        self, candidates: list[CandidateStrategy], hypotheses: list[Hypothesis]
    ) -> dict[str, float]:
        pass

    @abstractmethod
    def _enrich_candidates(
        self,
        candidates: list[CandidateStrategy],
        reasoning_state: ReasoningState,
        hypotheses: list[Hypothesis],
    ) -> list[CandidateStrategy]:
        pass

    @abstractmethod
    def _select_final_strategy(
        self, candidates: list[CandidateStrategy], scores: dict[str, float]
    ) -> ExecutionStrategy | None:
        pass

    @abstractmethod
    def _construct_session(
        self,
        context: PlanningContext,
        hypotheses: list[Hypothesis],
        candidates: list[CandidateStrategy],
        selected: ExecutionStrategy | None,
    ) -> PlanningSession:
        pass
