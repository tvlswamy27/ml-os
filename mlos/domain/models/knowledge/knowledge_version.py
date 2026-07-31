from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KnowledgeVersion:
    """
    Metadata capturing the version lineage, parent links, and rollbacks for a KnowledgeEntry.
    """

    version_number: int
    parent_entry_id: str | None
    timestamp: datetime
    change_summary: str
    reason: str
    rollback_reference: str | None = None
