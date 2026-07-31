from dataclasses import dataclass, field
from mlos.domain.models.base import BaseModel
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry

# Patch BaseModel to appear frozen to the dataclasses compiler at runtime
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = True  # type: ignore[attr-defined]


@dataclass(frozen=True)
class KnowledgeSession(BaseModel):  # type: ignore[misc]
    """
    Immutable representation of the outputs of a single knowledge cycle.
    """

    summary: str
    promoted_entries: list[KnowledgeEntry] = field(default_factory=list)
    conflicts: list[KnowledgeConflict] = field(default_factory=list)
    telemetry: KnowledgeTelemetry | None = None

    def to_dict(self) -> dict:
        """Serialize KnowledgeSession fields to YAML-serializable primitives."""
        data = super().to_dict()

        serialized_entries = []
        for e in self.promoted_entries:
            serialized_entries.append(
                {
                    "knowledge_id": e.knowledge_id,
                    "knowledge_type": e.knowledge_type.value,
                    "target_subsystem": e.target_subsystem,
                    "target_component": e.target_component,
                    "parameters": dict(e.parameters),
                    "source_learning_sessions": list(e.source_learning_sessions),
                    "evidence_summary": e.evidence_summary,
                    "version": {
                        "version_number": e.version.version_number,
                        "parent_entry_id": e.version.parent_entry_id,
                        "timestamp": e.version.timestamp.isoformat(),
                        "change_summary": e.version.change_summary,
                        "reason": e.version.reason,
                        "rollback_reference": e.version.rollback_reference,
                    },
                    "created_at": e.created_at.isoformat(),
                    "last_used": e.last_used.isoformat() if e.last_used else None,
                    "usage_count": e.usage_count,
                    "confidence": {
                        "score": e.confidence.score,
                        "uncertainty": e.confidence.uncertainty,
                        "support_count": e.confidence.support_count,
                        "usage_history_count": e.confidence.usage_history_count,
                        "explanation": e.confidence.explanation,
                    },
                    "status": e.status.value,
                    "usage_metadata": (
                        dict(e.usage_metadata) if e.usage_metadata else {}
                    ),
                }
            )
        data["promoted_entries"] = serialized_entries

        data["conflicts"] = [
            {
                "conflict_id": c.conflict_id,
                "subsystem": c.subsystem,
                "component": c.component,
                "parameter_name": c.parameter_name,
                "competing_values": list(c.competing_values),
                "resolution_applied": c.resolution_applied,
            }
            for c in self.conflicts
        ]
        return data


# Restore BaseModel configuration
if hasattr(BaseModel, "__dataclass_params__"):
    BaseModel.__dataclass_params__.frozen = False  # type: ignore[attr-defined]
