from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel
from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry
from mlos.domain.models.learning.learning_update import LearningUpdate

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class LearningSession(BaseModel):  # type: ignore[misc]
    """
    Immutable representation of the outputs of a single learning cycle.
    """

    summary: str
    updates: list[LearningUpdate] = field(default_factory=list)
    confidence: LearningConfidence | None = None
    telemetry: LearningTelemetry | None = None

    def to_dict(self) -> dict:
        """Serialize LearningSession fields to YAML-serializable primitives."""
        data = super().to_dict()
        if "updates" in data:
            serialized_updates = []
            for u in data["updates"]:
                ev = u["evidence"]
                serialized_updates.append(
                    {
                        "update_id": u["update_id"],
                        "update_type": (
                            u["update_type"].value
                            if hasattr(u["update_type"], "value")
                            else str(u["update_type"])
                        ),
                        "target_subsystem": u["target_subsystem"],
                        "target_component": u["target_component"],
                        "parameters": dict(u["parameters"]),
                        "evidence": {
                            "reflection_session_ids": list(
                                ev["reflection_session_ids"]
                            ),
                            "evaluation_session_ids": list(
                                ev["evaluation_session_ids"]
                            ),
                            "execution_session_ids": list(ev["execution_session_ids"]),
                            "metrics_used": list(ev["metrics_used"]),
                            "confidence_values": list(ev["confidence_values"]),
                            "frequency_counts": dict(ev["frequency_counts"]),
                            "trend_information": dict(ev["trend_information"]),
                            "supporting_observations": list(
                                ev["supporting_observations"]
                            ),
                        },
                    }
                )
            data["updates"] = serialized_updates
        return data


# Restore BaseModel configuration
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
