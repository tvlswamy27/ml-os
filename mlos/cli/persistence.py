"""
CLI Persistence helper.

Responsible for saving and loading lightweight project configurations.

Author: Vikram Tanakala
License: MIT
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING
import yaml
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService

if TYPE_CHECKING:
    from mlos.domain.models.reflection.reflection_session import ReflectionSession
    from mlos.domain.models.learning.learning_session import LearningSession
    from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
    from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """
    Search upwards from start_dir to find a directory containing a '.mlos' folder.
    """
    current = Path(start_dir or os.getcwd()).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".mlos").is_dir():
            return parent
    return None


def load_project_config(project_root: Path) -> dict | None:
    """
    Load project configurations from the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    if not config_file.is_file():
        return None
    with open(config_file, "r") as f:
        return yaml.safe_load(f) or {}


def save_project_config(project_root: Path, config: dict) -> None:
    """
    Save project configurations to the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def reconstruct_project_memory(project_root: Path) -> ProjectMemory | None:
    """
    Reconstruct ProjectMemory from the lightweight config on disk.
    """
    config = load_project_config(project_root)
    if config is None:
        return None

    memory_service = ProjectMemoryService()
    memory = memory_service.create(
        project_name=config.get("project_name", ""),
        project_goal=config.get("project_goal", ""),
    )

    if "current_stage" in config:
        memory.current_stage = config["current_stage"]
    if "completed_tasks" in config:
        memory.completed_tasks = config.get("completed_tasks", [])
    if "notes" in config:
        memory.notes = config.get("notes", [])

    dataset_path = config.get("dataset_path")
    if dataset_path:
        from mlos.domain.models.dataset import Dataset

        dataset = Dataset(
            path=dataset_path,
            target=config.get("target_column"),
        )
        memory.dataset = dataset

    if "reflection_sessions" in config:
        memory.reflection_sessions = [
            dict_to_reflection_session(s) for s in config["reflection_sessions"]
        ]

    if "learning_sessions" in config:
        memory.learning_sessions = [
            dict_to_learning_session(s) for s in config["learning_sessions"]
        ]

    if "knowledge_sessions" in config:
        memory.knowledge_sessions = [
            dict_to_knowledge_session(s) for s in config["knowledge_sessions"]
        ]

    if "knowledge_entries" in config:
        memory.knowledge_entries = [
            dict_to_knowledge_entry(e) for e in config["knowledge_entries"]
        ]

    return memory


def dict_to_reflection_session(data: dict) -> "ReflectionSession":
    """Helper to reconstruct a ReflectionSession from raw dict."""
    from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
    from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
    from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
    from mlos.domain.models.reflection.reflection_session import ReflectionSession

    insights = []
    for item in data.get("insights", []):
        insights.append(
            ReflectionInsight(
                insight_id=item.get("insight_id", ""),
                insight_type=item.get("insight_type", ""),
                severity=item.get("severity", ""),
                summary=item.get("summary", ""),
                evidence=tuple(item.get("evidence", ())),
                confidence=item.get("confidence", 1.0),
            )
        )

    feedback = []
    for item in data.get("feedback", []):
        feedback.append(
            ReflectionFeedback(
                feedback_id=item.get("feedback_id", ""),
                target_subsystem=item.get("target_subsystem", ""),
                target_component=item.get("target_component", ""),
                action_type=item.get("action_type", ""),
                parameters=dict(item.get("parameters", {})),
                priority=item.get("priority", ""),
                reason=item.get("reason", ""),
                expected_outcome=item.get("expected_outcome", ""),
            )
        )

    conf_data = data.get("confidence")
    confidence = None
    if conf_data:
        confidence = ReflectionConfidence(
            score=conf_data.get("score", 0.0),
            uncertainty=conf_data.get("uncertainty", 0.0),
            evidence=tuple(conf_data.get("evidence", ())),
            explanation=conf_data.get("explanation", ""),
            accepted=conf_data.get("accepted", False),
        )

    session = ReflectionSession(
        summary=data.get("summary", ""),
        insights=insights,
        feedback=feedback,
        confidence=confidence,
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )

    return session


def dict_to_learning_session(data: dict) -> "LearningSession":
    """Helper to reconstruct a LearningSession from raw dict."""
    from mlos.domain.models.learning.learning_update_type import LearningUpdateType
    from mlos.domain.models.learning.learning_evidence import LearningEvidence
    from mlos.domain.models.learning.learning_update import LearningUpdate
    from mlos.domain.models.learning.learning_confidence import LearningConfidence
    from mlos.domain.models.learning.learning_session import LearningSession

    updates = []
    for u in data.get("updates", []):
        ev_data = u.get("evidence", {})
        evidence = LearningEvidence(
            reflection_session_ids=tuple(ev_data.get("reflection_session_ids", ())),
            evaluation_session_ids=tuple(ev_data.get("evaluation_session_ids", ())),
            execution_session_ids=tuple(ev_data.get("execution_session_ids", ())),
            metrics_used=tuple(ev_data.get("metrics_used", ())),
            confidence_values=tuple(ev_data.get("confidence_values", ())),
            frequency_counts=dict(ev_data.get("frequency_counts", {})),
            trend_information=dict(ev_data.get("trend_information", {})),
            supporting_observations=tuple(ev_data.get("supporting_observations", ())),
        )
        u_type = LearningUpdateType(u.get("update_type"))
        updates.append(
            LearningUpdate(
                update_id=u.get("update_id", ""),
                update_type=u_type,
                target_subsystem=u.get("target_subsystem", ""),
                target_component=u.get("target_component", ""),
                parameters=dict(u.get("parameters", {})),
                evidence=evidence,
            )
        )

    conf_data = data.get("confidence")
    confidence = None
    if conf_data:
        confidence = LearningConfidence(
            score=conf_data.get("score", 0.0),
            uncertainty=conf_data.get("uncertainty", 0.0),
            evidence=tuple(conf_data.get("evidence", ())),
            explanation=conf_data.get("explanation", ""),
            accepted=conf_data.get("accepted", False),
        )

    session = LearningSession(
        summary=data.get("summary", ""), updates=updates, confidence=confidence
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )

    return session


def dict_to_knowledge_session(data: dict) -> "KnowledgeSession":
    """Helper to reconstruct a KnowledgeSession from raw dict."""
    from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
    from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict

    conflicts = []
    for c in data.get("conflicts", []):
        conflicts.append(
            KnowledgeConflict(
                conflict_id=c.get("conflict_id", ""),
                subsystem=c.get("subsystem", ""),
                component=c.get("component", ""),
                parameter_name=c.get("parameter_name", ""),
                competing_values=tuple(c.get("competing_values", ())),
                resolution_applied=c.get("resolution_applied", ""),
            )
        )

    promoted = [dict_to_knowledge_entry(e) for e in data.get("promoted_entries", [])]

    session = KnowledgeSession(
        summary=data.get("summary", ""), promoted_entries=promoted, conflicts=conflicts
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )
    return session


def dict_to_knowledge_entry(data: dict) -> "KnowledgeEntry":
    """Helper to reconstruct a KnowledgeEntry from raw dict."""
    from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
    from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
    from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
    from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
    from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
    from datetime import datetime

    v_data = data.get("version", {})
    version = KnowledgeVersion(
        version_number=v_data.get("version_number", 1),
        parent_entry_id=v_data.get("parent_entry_id"),
        timestamp=(
            datetime.fromisoformat(v_data["timestamp"])
            if "timestamp" in v_data
            else datetime.now()
        ),
        change_summary=v_data.get("change_summary", ""),
        reason=v_data.get("reason", ""),
        rollback_reference=v_data.get("rollback_reference"),
    )

    c_data = data.get("confidence", {})
    confidence = KnowledgeConfidence(
        score=c_data.get("score", 0.0),
        uncertainty=c_data.get("uncertainty", 0.0),
        support_count=c_data.get("support_count", 0),
        usage_history_count=c_data.get("usage_history_count", 0),
        explanation=c_data.get("explanation", ""),
    )

    k_type = KnowledgeEntryType(data["knowledge_type"])
    k_status = KnowledgeStatus(data["status"])

    entry = KnowledgeEntry(
        knowledge_id=data.get("knowledge_id", ""),
        knowledge_type=k_type,
        target_subsystem=data.get("target_subsystem", ""),
        target_component=data.get("target_component", ""),
        parameters=dict(data.get("parameters", {})),
        source_learning_sessions=tuple(data.get("source_learning_sessions", ())),
        evidence_summary=data.get("evidence_summary", ""),
        version=version,
        created_at=(
            datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now()
        ),
        last_used=(
            datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        ),
        usage_count=data.get("usage_count", 0),
        confidence=confidence,
        status=k_status,
        usage_metadata=dict(data.get("usage_metadata", {})),
    )
    return entry


def update_project_config_from_memory(
    project_root: Path, memory: ProjectMemory
) -> None:
    """
    Sync memory back into the lightweight configuration file.
    """
    config = load_project_config(project_root) or {}
    config["project_name"] = memory.project_name
    config["project_goal"] = memory.project_goal
    config["current_stage"] = memory.current_stage
    config["completed_tasks"] = memory.completed_tasks
    config["notes"] = memory.notes

    if memory.dataset:
        config["dataset_path"] = str(memory.dataset.path)
        config["target_column"] = memory.dataset.target

    if memory.reflection_sessions:
        config["reflection_sessions"] = [
            s.to_dict() for s in memory.reflection_sessions
        ]

    if memory.learning_sessions:
        config["learning_sessions"] = [s.to_dict() for s in memory.learning_sessions]

    if memory.knowledge_sessions:
        config["knowledge_sessions"] = [s.to_dict() for s in memory.knowledge_sessions]

    if memory.knowledge_entries:
        serialized_entries = []
        for e in memory.knowledge_entries:
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
        config["knowledge_entries"] = serialized_entries

    save_project_config(project_root, config)
