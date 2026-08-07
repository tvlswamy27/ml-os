"""
ExecutionPolicy domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.execution_strategy import ExecutionStrategy
from mlos.domain.models.meta_reasoning.explainability import DecisionTrace
from mlos.domain.models.meta_reasoning.resource_allocation import ResourceAllocation


@dataclass(frozen=True)
class ExecutionPolicy:
    """
    Immutable specification of ExecutionStrategy, ResourceAllocation and DecisionTrace per subsystem.
    """

    subsystem: SubsystemName
    strategy: ExecutionStrategy
    resources: ResourceAllocation
    trace: DecisionTrace
