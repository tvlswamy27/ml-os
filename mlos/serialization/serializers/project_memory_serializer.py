"""
VersionedSerializer for ProjectMemory.

Author: Antigravity
License: MIT
"""

from typing import Any

from mlos.domain.models.project_memory import ProjectMemory
from mlos.serialization.version import VersionedSerializer


class ProjectMemorySerializer(VersionedSerializer):
    """Serializer converting ProjectMemory models to/from versioned dictionaries."""

    def serialize(self, model: Any) -> dict[str, Any]:
        if not isinstance(model, ProjectMemory):
            raise TypeError("Expected ProjectMemory instance.")

        # Import helper serialization methods locally to avoid circular imports
        from mlos.cli.persistence import (
            execution_snapshot_to_dict,
            feature_session_to_dict,
            meta_session_to_dict,
        )

        config: dict[str, Any] = {
            "project_name": model.project_name,
            "project_goal": model.project_goal,
            "current_stage": model.current_stage,
            "completed_tasks": list(model.completed_tasks),
            "notes": list(model.notes),
        }

        if model.dataset:
            config["dataset_path"] = str(model.dataset.path)
            config["target_column"] = model.dataset.target
            config["dataset"] = {
                "path": str(model.dataset.path),
                "rows": model.dataset.rows,
                "columns": model.dataset.columns,
                "target": model.dataset.target,
                "problem_type": model.dataset.problem_type,
                "categorical_columns": list(model.dataset.categorical_columns),
                "numerical_columns": list(model.dataset.numerical_columns),
                "missing_values": dict(model.dataset.missing_values),
                "duplicate_rows": model.dataset.duplicate_rows,
                "unique_values": dict(model.dataset.unique_values),
                "missing_percentages": dict(model.dataset.missing_percentages),
                "column_types": dict(model.dataset.column_types),
            }

        if model.project_profile:
            serialized_risks = []
            for r in model.project_profile.risks:
                serialized_risks.append(
                    {
                        "title": r.title,
                        "severity": r.severity,
                        "description": r.description,
                        "recommendation": r.recommendation,
                        "affected_columns": (
                            list(r.affected_columns) if r.affected_columns else None
                        ),
                    }
                )
            config["project_profile"] = {
                "problem_type": model.project_profile.problem_type,
                "complexity": model.project_profile.complexity,
                "baseline_models": list(model.project_profile.baseline_models),
                "risks": serialized_risks,
            }

        if model.pipeline:
            config["pipeline"] = {
                "entrypoint_path": str(model.pipeline.entrypoint_path),
                "configuration_path": (
                    str(model.pipeline.configuration_path)
                    if model.pipeline.configuration_path
                    else None
                ),
            }

        if model.reflection_sessions:
            config["reflection_sessions"] = [
                s.to_dict() for s in model.reflection_sessions
            ]

        if model.learning_sessions:
            config["learning_sessions"] = [s.to_dict() for s in model.learning_sessions]

        if model.knowledge_sessions:
            config["knowledge_sessions"] = [
                s.to_dict() for s in model.knowledge_sessions
            ]

        if model.knowledge_entries:
            serialized_entries = []
            for e in model.knowledge_entries:
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

        if model.feature_sessions:
            config["feature_sessions"] = [
                feature_session_to_dict(s) for s in model.feature_sessions
            ]

        if model.meta_sessions:
            config["meta_sessions"] = [
                meta_session_to_dict(s) for s in model.meta_sessions
            ]

        if model.execution_snapshots:
            config["execution_snapshots"] = [
                execution_snapshot_to_dict(s) for s in model.execution_snapshots
            ]

        return config

    def deserialize(self, data: dict[str, Any]) -> Any:
        # Import helper deserialization methods locally to avoid circular imports
        from mlos.cli.persistence import (
            dict_to_execution_snapshot,
            dict_to_feature_session,
            dict_to_knowledge_entry,
            dict_to_knowledge_session,
            dict_to_learning_session,
            dict_to_meta_session,
            dict_to_reflection_session,
        )
        from mlos.domain.models.dataset import Dataset
        from mlos.domain.models.pipeline import Pipeline
        from mlos.domain.models.project_profile import ProjectProfile
        from mlos.domain.services.project_memory_service import ProjectMemoryService

        memory_service = ProjectMemoryService()
        memory = memory_service.create(
            project_name=data.get("project_name", ""),
            project_goal=data.get("project_goal", ""),
        )

        memory.current_stage = data.get("current_stage", "Project Initialization")
        memory.completed_tasks = data.get("completed_tasks", [])
        memory.notes = data.get("notes", [])

        dataset_path = data.get("dataset_path")
        if "dataset" in data and isinstance(data["dataset"], dict):
            ds = data["dataset"]
            memory.dataset = Dataset(
                path=ds.get("path", dataset_path or ""),
                rows=ds.get("rows", 0),
                columns=ds.get("columns", 0),
                target=ds.get("target", data.get("target_column")),
                problem_type=ds.get("problem_type"),
                categorical_columns=list(ds.get("categorical_columns", [])),
                numerical_columns=list(ds.get("numerical_columns", [])),
                missing_values=dict(ds.get("missing_values", {})),
                duplicate_rows=ds.get("duplicate_rows", 0),
                unique_values=dict(ds.get("unique_values", {})),
                missing_percentages=dict(ds.get("missing_percentages", {})),
                column_types=dict(ds.get("column_types", {})),
            )
        elif dataset_path:
            memory.dataset = Dataset(
                path=dataset_path,
                target=data.get("target_column"),
            )

        if "project_profile" in data:
            pp = data["project_profile"]
            from mlos.domain.models.risk import Risk

            deserialized_risks = []
            if "risks" in pp:
                for r in pp["risks"]:
                    deserialized_risks.append(
                        Risk(
                            title=r.get("title", ""),
                            severity=r.get("severity", ""),
                            description=r.get("description", ""),
                            recommendation=r.get("recommendation", ""),
                            affected_columns=r.get("affected_columns"),
                        )
                    )

            memory.project_profile = ProjectProfile(
                problem_type=pp.get("problem_type"),
                complexity=pp.get("complexity"),
                baseline_models=list(pp.get("baseline_models", [])),
                risks=deserialized_risks,
            )

        if "pipeline" in data:
            from pathlib import Path

            pl = data["pipeline"]
            entrypoint = pl.get("entrypoint_path") or pl.get("name") or "pipeline.py"
            config_path = pl.get("configuration_path")
            memory.pipeline = Pipeline(
                entrypoint_path=Path(entrypoint),
                configuration_path=Path(config_path) if config_path else None,
            )

        if "reflection_sessions" in data:
            memory.reflection_sessions = [
                dict_to_reflection_session(s) for s in data["reflection_sessions"]
            ]

        if "learning_sessions" in data:
            memory.learning_sessions = [
                dict_to_learning_session(s) for s in data["learning_sessions"]
            ]

        if "knowledge_sessions" in data:
            memory.knowledge_sessions = [
                dict_to_knowledge_session(s) for s in data["knowledge_sessions"]
            ]

        if "knowledge_entries" in data:
            memory.knowledge_entries = [
                dict_to_knowledge_entry(e) for e in data["knowledge_entries"]
            ]

        if "feature_sessions" in data:
            memory.feature_sessions = [
                dict_to_feature_session(s) for s in data["feature_sessions"]
            ]

        if "meta_sessions" in data:
            memory.meta_sessions = [
                dict_to_meta_session(s) for s in data["meta_sessions"]
            ]

        if "execution_snapshots" in data:
            memory.execution_snapshots = [
                dict_to_execution_snapshot(s) for s in data["execution_snapshots"]
            ]

        return memory
