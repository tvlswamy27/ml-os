"""
ReflectionSession domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.base import BaseModel
from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class ReflectionSession(BaseModel):  # type: ignore[misc]
    """
    Immutable representation of the reasoning outputs of a single reflection cycle.
    """

    summary: str
    insights: list[ReflectionInsight] = field(default_factory=list)
    feedback: list[ReflectionFeedback] = field(default_factory=list)
    confidence: ReflectionConfidence | None = None
    telemetry: ReflectionTelemetry | None = None


# Restore BaseModel to original non-frozen state for other subclasses
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
