"""
ReflectionAlgorithm interface using the Template Method pattern.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
from mlos.domain.models.reflection.reflection_context import ReflectionContext
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_reasoning_state import (
    ReflectionReasoningState,
)
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback


class ReflectionAlgorithm(ABC):
    """
    Abstract Base Class defining the template method and interface for reflection reasoning.
    """

    @abstractmethod
    def can_reflect(self, context: ReflectionContext) -> bool:
        """Verify if this algorithm is capable of reflecting over the given context."""
        pass

    def reflect(self, context: ReflectionContext) -> ReflectionSession:
        """
        Template Method: Coordinates the sequence of protected reflection phases.
        Consumes and updates ReflectionReasoningState.
        """
        # Phase 1: Build typed reasoning state from context
        state = self._analyze_history(context)

        # Phase 2: Perform multi-run comparisons, returning updated state
        state = self._compare_runs(context, state)

        # Phase 3: Detect patterns, successes, and failures to generate insights
        insights = self._detect_patterns(context, state)

        # Phase 4: Formulate structured feedback recommendations
        feedback = self._generate_recommendations(context, state, insights)

        # Phase 5: Build final frozen ReflectionSession
        return self._construct_session(insights, feedback, state)

    @abstractmethod
    def _analyze_history(self, context: ReflectionContext) -> ReflectionReasoningState:
        """Step 1: Extract, index, and organize raw metric histories for querying."""
        pass

    @abstractmethod
    def _compare_runs(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> ReflectionReasoningState:
        """Step 2: Contrast the latest evaluation with past runs, updating the state."""
        pass

    @abstractmethod
    def _detect_patterns(
        self, context: ReflectionContext, state: ReflectionReasoningState
    ) -> tuple[ReflectionInsight, ...]:
        """Step 3: Analyze performance transitions to generate unified ReflectionInsights."""
        pass

    @abstractmethod
    def _generate_recommendations(
        self,
        context: ReflectionContext,
        state: ReflectionReasoningState,
        insights: tuple[ReflectionInsight, ...],
    ) -> tuple[ReflectionFeedback, ...]:
        """Step 4: Translate insights into structured ReflectionFeedback recommendations."""
        pass

    @abstractmethod
    def _construct_session(
        self,
        insights: tuple[ReflectionInsight, ...],
        feedback: tuple[ReflectionFeedback, ...],
        state: ReflectionReasoningState,
    ) -> ReflectionSession:
        """Step 5: Assemble insights and feedback into a final ReflectionSession."""
        pass
