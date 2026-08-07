from dataclasses import dataclass, field

from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType


@dataclass(frozen=True)
class ProposedKnowledgeUpdate:
    """
    Strongly typed, immutable representation of a proposed update parsed from learning feedback.
    """

    update_id: str
    entry_type: KnowledgeEntryType
    target_subsystem: str
    target_component: str
    parameters: dict[str, str]
    learning_session_id: str
    confidence_score: float
    evidence_summary: str


@dataclass(frozen=True)
class KnowledgeReasoningState:
    """
    Typed reasoning state carrying parsed updates, conflicts, and resolutions across algorithm phases.
    """

    incoming_updates: tuple[ProposedKnowledgeUpdate, ...] = field(default_factory=tuple)
    detected_conflicts: tuple[KnowledgeConflict, ...] = field(default_factory=tuple)
    resolved_entries: tuple[KnowledgeEntry, ...] = field(default_factory=tuple)
    current_max_version: int = 0
