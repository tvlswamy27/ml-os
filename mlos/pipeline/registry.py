"""
Pipeline Registry and Persistence Engine for ML-OS.

Supports saving, loading, exporting, cloning, listing, and deleting reusable ML pipelines.

Author: Antigravity
License: MIT
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib


@dataclass
class PipelineRecord:
    """Metadata record for a registered pipeline."""

    pipeline_id: str
    version: str
    name: str
    created_at: str
    feature_transformations: list[str] = field(default_factory=list)
    model_id: str = ""
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)


class PipelineRegistry:
    """
    Manages persistent, versioned ML pipelines in .mlos/pipelines/.
    """

    def __init__(self, workspace_root: Path | str = "."):
        self.workspace_root = Path(workspace_root)
        self.pipeline_dir = self.workspace_root / ".mlos" / "pipelines"
        self.pipeline_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.pipeline_dir / "pipelines.json"
        self._load_registry()

    def _load_registry(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        if self.metadata_file.exists():
            try:
                self.records = json.loads(
                    self.metadata_file.read_text(encoding="utf-8")
                )
            except Exception:
                self.records = {}

    def _save_registry(self) -> None:
        self.metadata_file.write_text(
            json.dumps(self.records, indent=2), encoding="utf-8"
        )

    def save_pipeline(
        self,
        pipeline_id: str,
        pipeline_object: Any,
        model_id: str,
        metrics: dict[str, float],
        feature_transformations: list[str] | None = None,
        hyperparameters: dict[str, Any] | None = None,
    ) -> PipelineRecord:
        """Save a fitted sklearn/ML-OS pipeline object to disk."""
        target_folder = self.pipeline_dir / pipeline_id
        target_folder.mkdir(parents=True, exist_ok=True)

        model_file = target_folder / "pipeline.joblib"
        joblib.dump(pipeline_object, model_file)

        record = PipelineRecord(
            pipeline_id=pipeline_id,
            version="1.0.0",
            name=f"Pipeline-{pipeline_id}",
            created_at=datetime.utcnow().isoformat(),
            feature_transformations=feature_transformations or [],
            model_id=model_id,
            hyperparameters=hyperparameters or {},
            metrics=metrics,
            artifacts={"pipeline_joblib": str(model_file)},
        )

        self.records[pipeline_id] = {
            "pipeline_id": record.pipeline_id,
            "version": record.version,
            "name": record.name,
            "created_at": record.created_at,
            "feature_transformations": record.feature_transformations,
            "model_id": record.model_id,
            "hyperparameters": record.hyperparameters,
            "metrics": record.metrics,
            "artifacts": record.artifacts,
        }
        self._save_registry()
        return record

    def load_pipeline(self, pipeline_id: str) -> Any:
        """Load a pipeline object from disk by ID."""
        target_folder = self.pipeline_dir / pipeline_id
        model_file = target_folder / "pipeline.joblib"
        if not model_file.exists():
            raise FileNotFoundError(
                f"Pipeline '{pipeline_id}' not found at {model_file}"
            )
        return joblib.load(model_file)

    def export_pipeline(self, pipeline_id: str, export_path: Path | str) -> str:
        """Export a pipeline directory into an archive file."""
        target_folder = self.pipeline_dir / pipeline_id
        if not target_folder.exists():
            raise FileNotFoundError(f"Pipeline '{pipeline_id}' not found.")

        archive = shutil.make_archive(str(export_path), "zip", target_folder)
        return archive

    def clone_pipeline(self, source_id: str, new_id: str) -> PipelineRecord:
        """Clone an existing pipeline under a new ID."""
        src_folder = self.pipeline_dir / source_id
        dst_folder = self.pipeline_dir / new_id
        if not src_folder.exists():
            raise FileNotFoundError(f"Source pipeline '{source_id}' not found.")

        shutil.copytree(src_folder, dst_folder)
        rec_data = dict(self.records.get(source_id, {}))
        rec_data["pipeline_id"] = new_id
        rec_data["created_at"] = datetime.utcnow().isoformat()
        rec_data["artifacts"] = {"pipeline_joblib": str(dst_folder / "pipeline.joblib")}

        self.records[new_id] = rec_data
        self._save_registry()

        return PipelineRecord(**rec_data)

    def list_pipelines(self) -> list[dict[str, Any]]:
        """List metadata for all registered pipelines."""
        return list(self.records.values())

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a registered pipeline."""
        target_folder = self.pipeline_dir / pipeline_id
        if target_folder.exists():
            shutil.rmtree(target_folder)

        if pipeline_id in self.records:
            del self.records[pipeline_id]
            self._save_registry()
            return True
        return False
