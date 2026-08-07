from dataclasses import dataclass, field
from datetime import datetime

from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion


@dataclass(frozen=True)
class KnowledgeEntry:
    """
    Represents an immutable, version-tracked system optimization policy entry.
    """

    knowledge_id: str
    knowledge_type: KnowledgeEntryType
    target_subsystem: str
    target_component: str
    parameters: dict[str, str]
    source_learning_sessions: tuple[str, ...]
    evidence_summary: str
    version: KnowledgeVersion
    created_at: datetime
    last_used: datetime | None
    usage_count: int
    confidence: KnowledgeConfidence
    status: KnowledgeStatus
    usage_metadata: dict[str, str] = field(default_factory=dict)
