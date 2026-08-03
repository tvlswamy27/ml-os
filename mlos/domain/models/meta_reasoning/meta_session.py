"""
MetaSession domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.models.base import BaseModel
from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.meta_reasoning_state import MetaReasoningState
from mlos.domain.models.meta_reasoning.policy_version import PolicyVersion

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class MetaSession(BaseModel):  # type: ignore[misc]
    """
    Immutable representation of a Meta-Reasoning session.
    """

    context: MetaContext
    reasoning_state: MetaReasoningState
    policy_version: PolicyVersion
    execution_lifecycle: ExecutionLifecycle = ExecutionLifecycle.PLANNED


# Restore BaseModel to original non-frozen state for other subclasses
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
