"""
Centralized Artifact Registry for ML-OS.

Author: Antigravity
License: MIT
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml


@dataclass(frozen=True)
class ExecutionArtifact:
    """Representing structured artifact metadata and physical storage path."""

    artifact_id: UUID
    name: str
    artifact_type: str  # e.g. MODEL, PREPROCESSOR, REPORT, EXPLAINABILITY, DATASET, CHECKPOINT, DEPLOYMENT
    file_path: str
    version: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": str(self.artifact_id),
            "name": self.name,
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionArtifact":
        return cls(
            artifact_id=UUID(data["artifact_id"]),
            name=data["name"],
            artifact_type=data["artifact_type"],
            file_path=data["file_path"],
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


class ArtifactRegistry:
    """
    Registry that organizes, copies, versions, and persists outputs.
    """

    def __init__(self, project_path: str) -> None:
        self.project_path = Path(project_path)
        self.artifacts_dir = self.project_path / "artifacts"
        self.registry_file = self.project_path / ".mlos" / "artifacts_registry.yaml"
        self._artifacts: dict[str, ExecutionArtifact] = {}
        self.load()

    def register_artifact(
        self,
        name: str,
        artifact_type: str,  # e.g. MODEL, PREPROCESSOR, REPORT, EXPLAINABILITY, DATASET, CHECKPOINT, DEPLOYMENT
        source_file_path: Path,
        version: str = "1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionArtifact:
        """
        Register a new output file, copying it into the organized artifacts folder,
        and persisting metadata to the index log.
        """
        # Map artifact_type to corresponding directory name
        # types: MODEL -> models, PREPROCESSOR -> preprocessors, REPORT -> reports,
        # EXPLAINABILITY -> explainability, DATASET -> datasets, CHECKPOINT -> checkpoints, DEPLOYMENT -> deployments
        dir_name = artifact_type.lower()
        if not dir_name.endswith("s") and dir_name != "explainability":
            dir_name = dir_name + "s"

        target_dir = self.artifacts_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file_path = target_dir / source_file_path.name

        # Ensure source file exists before copying
        if source_file_path.exists():
            if source_file_path.resolve() != target_file_path.resolve():
                shutil.copy2(source_file_path, target_file_path)
        else:
            # If source file does not exist, touch the target path so the file exists
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file_path, "w") as f:
                f.write("")

        # Create structured execution artifact metadata
        artifact = ExecutionArtifact(
            artifact_id=uuid4(),
            name=name,
            artifact_type=artifact_type.upper(),
            file_path=str(target_file_path.relative_to(self.project_path)),
            version=version,
            created_at=datetime.now(),
            metadata=metadata or {},
        )

        self._artifacts[str(artifact.artifact_id)] = artifact
        self.save()

        # Publish event to GlobalEventBus
        from mlos.communication.event_bus import GlobalEventBus

        GlobalEventBus().publish(
            event_type="ArtifactRegistered",
            source="ArtifactRegistry",
            payload={
                "artifact_id": str(artifact.artifact_id),
                "name": name,
                "type": artifact.artifact_type,
            },
        )

        return artifact

    def get_artifact(self, artifact_id: UUID) -> ExecutionArtifact | None:
        """Fetch registered artifact by its unique ID."""
        return self._artifacts.get(str(artifact_id))

    def list_artifacts(
        self, artifact_type: str | None = None
    ) -> list[ExecutionArtifact]:
        """List all artifacts, optionally filtering by type."""
        all_art = list(self._artifacts.values())
        if artifact_type:
            all_art = [
                a for a in all_art if a.artifact_type.upper() == artifact_type.upper()
            ]
        return all_art

    def save(self) -> None:
        """Persist register to file."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.to_dict() for k, v in self._artifacts.items()}
        with open(self.registry_file, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def load(self) -> None:
        """Load registered artifacts from disk."""
        if not self.registry_file.exists():
            return
        try:
            with open(self.registry_file, "r") as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                self._artifacts = {
                    k: ExecutionArtifact.from_dict(v) for k, v in data.items()
                }
        except Exception:
            pass
