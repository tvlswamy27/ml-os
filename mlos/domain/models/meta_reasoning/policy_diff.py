"""
PolicyDiff domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class PolicyDiff:
    """
    Immutable representation of difference changes between two policies or schedules.
    """

    source_policy_id: UUID
    target_policy_id: UUID
    added_policies: tuple[str, ...] = field(default_factory=tuple)
    removed_policies: tuple[str, ...] = field(default_factory=tuple)
    modified_providers: dict[str, tuple[str, str]] = field(default_factory=dict)
    modified_modes: dict[str, tuple[str, str]] = field(default_factory=dict)
    modified_objectives: dict[str, tuple[float, float]] = field(default_factory=dict)
    modified_resources: dict[str, tuple[float, float]] = field(default_factory=dict)
    schedule_modified: bool = False
