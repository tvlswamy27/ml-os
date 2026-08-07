from abc import ABC, abstractmethod

from mlos.domain.models.knowledge.knowledge_context import KnowledgeContext
from mlos.domain.models.knowledge.knowledge_reasoning_state import (
    KnowledgeReasoningState,
)
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession


class KnowledgeAlgorithm(ABC):
    """
    Base class defining the Template Method reasoning pipeline for the Knowledge Subsystem.
    """

    @abstractmethod
    def can_manage(self, context: KnowledgeContext) -> bool:
        """Determines if the algorithm can execute given the context."""

    def manage(self, context: KnowledgeContext) -> KnowledgeSession:
        """
        Template Method: Runs structured knowledge phases sequentially.
        """
        # Phase 1: Analyze accepted learning updates
        state = self._analyze_updates(context)

        # Phase 2: Detect duplicate or conflicting knowledge
        state = self._detect_conflicts(context, state)

        # Phase 3: Resolve conflicts
        state = self._resolve_conflicts(context, state)

        # Phase 4: Determine promotions
        state = self._determine_promotions(context, state)

        # Phase 5: Version accepted knowledge
        state = self._version_knowledge(context, state)

        # Phase 6: Build confidence
        confidence_details = self._build_confidence(context, state)

        # Phase 7: Construct session
        return self._construct_session(state, confidence_details)

    @abstractmethod
    def _analyze_updates(self, context: KnowledgeContext) -> KnowledgeReasoningState:
        """Parses incoming learning updates into strongly typed ProposedKnowledgeUpdate objects."""

    @abstractmethod
    def _detect_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Scans incoming updates and existing entries to identify competing parameter settings."""

    @abstractmethod
    def _resolve_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Resolves overlapping parameter configurations using V1 deterministic priority rules."""

    @abstractmethod
    def _determine_promotions(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Decides which updates meet the promotional threshold (e.g. learning confidence)."""

    @abstractmethod
    def _version_knowledge(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Increments version counters and assigns unique parent entry ID links."""

    @abstractmethod
    def _build_confidence(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> dict:
        """Calculates final confidence for each promoted knowledge entry."""

    @abstractmethod
    def _construct_session(
        self, state: KnowledgeReasoningState, confidence_details: dict
    ) -> KnowledgeSession:
        """Assembles variables into the final, frozen KnowledgeSession object."""


class_names = ["KnowledgeAlgorithm"]
