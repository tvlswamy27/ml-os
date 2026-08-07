from abc import ABC, abstractmethod

from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_reasoning_state import LearningReasoningState
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update import LearningUpdate


class LearningAlgorithm(ABC):
    """
    Base class defining the Template Method reasoning pipeline for Learning.
    """

    @abstractmethod
    def can_learn(self, context: LearningContext) -> bool:
        """Determines if the algorithm can execute given the context."""

    def learn(self, context: LearningContext) -> LearningSession:
        """
        Template Method: Runs structured learning phases sequentially.
        """
        # Phase 1: Compile historical reflection feedback stats
        state = self._analyze_feedback(context)

        # Phase 2: Identify recurring failure/success patterns
        state = self._group_patterns(context, state)

        # Phase 3: Select and rank learning candidates based on priorities
        state = self._rank_learning_candidates(context, state)

        # Phase 4: Validate updates against conflict rules
        state = self._validate_candidates(context, state)

        # Phase 5: Build final updates
        updates = self._generate_learning_updates(context, state)

        # Phase 6: Assess overall confidence
        confidence = self._build_confidence(context, state)

        return self._construct_session(updates, confidence, state)

    @abstractmethod
    def _analyze_feedback(self, context: LearningContext) -> LearningReasoningState:
        """Processes raw feedback objects into a strongly typed FeedbackStats model."""

    @abstractmethod
    def _group_patterns(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Groups repeated action requests to calculate failure/success rates."""

    @abstractmethod
    def _rank_learning_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Sorts candidates by priority ('CRITICAL', 'HIGH') and weight support."""

    @abstractmethod
    def _validate_candidates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningReasoningState:
        """Validates updates to ensure they don't contradict or undo baseline constraints."""

    @abstractmethod
    def _generate_learning_updates(
        self, context: LearningContext, state: LearningReasoningState
    ) -> tuple[LearningUpdate, ...]:
        """Translates validated candidates to structured, machine-readable LearningUpdate objects."""

    @abstractmethod
    def _build_confidence(
        self, context: LearningContext, state: LearningReasoningState
    ) -> LearningConfidence:
        """Calculates uncertainty and derives the accepted check status."""

    @abstractmethod
    def _construct_session(
        self,
        updates: tuple[LearningUpdate, ...],
        confidence: LearningConfidence,
        state: LearningReasoningState,
    ) -> LearningSession:
        """Assembles variables into the final, frozen LearningSession object."""
