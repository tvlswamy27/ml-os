"""
ExecutionStrategy domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.base import BaseModel

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class ExecutionStrategy(BaseModel):  # type: ignore[misc]
    """
    The selected, immutable execution strategy for compiling and running the workflow.
    """

    strategy_name: str

    topological_steps: list[str] = field(default_factory=list)

    parameters: dict[str, str] = field(default_factory=dict)


# Restore BaseModel to original non-frozen state for other subclasses
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
