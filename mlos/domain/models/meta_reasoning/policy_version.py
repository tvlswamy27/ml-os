"""
PolicyVersion domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PolicyVersion:
    """
    Immutable representation of policy version lineage.
    """

    policy_id: UUID
    version: int
    parent_policy_id: UUID | None
    generated_by: str
    generated_at: datetime
    superseded_by: UUID | None
    effective_from: datetime
