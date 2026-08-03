"""
ExecutionSchedule domain models.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.enums.subsystem_name import SubsystemName


@dataclass(frozen=True)
class ScheduleNode:
    """
    Subsystem schedule configuration details.
    """

    node_id: str
    subsystem: SubsystemName
    execution_condition: str  # "ALWAYS", "ON_PLANNING_SUCCESS", etc.
    is_deferred: bool


@dataclass(frozen=True)
class ScheduleDependency:
    """
    Dependency connection between schedule nodes.
    """

    parent_node_id: str
    child_node_id: str
    dependency_type: str  # "SEQUENTIAL", "CONDITIONAL"


@dataclass(frozen=True)
class ExecutionSchedule:
    """
    Orchestrated scheduler graph matching topological execution orders.
    """

    nodes: tuple[ScheduleNode, ...]
    dependencies: tuple[ScheduleDependency, ...]
    max_parallel_workers: int
