"""
Versioned Model Registry for ML-OS.

Manages model versions, deployment stages (staging, production, archived), approval status,
and rollback candidates.

Author: Antigravity
License: MIT
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ModelVersionRecord:
    """Model version metadata record in registry."""

    model_id: str
    version: str
    stage: str = "staging"  # "staging", "production", "archived", "rollback"
    approval_status: str = "PENDING"  # "PENDING", "APPROVED", "REJECTED"
    metrics: dict[str, float] = field(default_factory=dict)
    created_at: str = ""
    notes: str = ""


class ModelRegistry:
    """
    Model Registry managing version lifecycle and deployment status.
    """

    def __init__(self, workspace_root: Path | str = "."):
        self.workspace_root = Path(workspace_root)
        self.registry_dir = self.workspace_root / ".mlos" / "model_registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.registry_dir / "model_registry.json"
        self._load()

    def _load(self) -> None:
        self.models: dict[str, dict[str, Any]] = {}
        if self.registry_file.exists():
            try:
                self.models = json.loads(self.registry_file.read_text(encoding="utf-8"))
            except Exception:
                self.models = {}

    def _save(self) -> None:
        self.registry_file.write_text(
            json.dumps(self.models, indent=2), encoding="utf-8"
        )

    def register_version(
        self,
        model_id: str,
        version: str,
        metrics: dict[str, float],
        stage: str = "staging",
        notes: str = "",
    ) -> ModelVersionRecord:
        """Register a new model version."""
        key = f"{model_id}:{version}"
        rec = ModelVersionRecord(
            model_id=model_id,
            version=version,
            stage=stage,
            approval_status="APPROVED" if stage == "production" else "PENDING",
            metrics=metrics,
            created_at=datetime.utcnow().isoformat(),
            notes=notes,
        )
        self.models[key] = {
            "model_id": rec.model_id,
            "version": rec.version,
            "stage": rec.stage,
            "approval_status": rec.approval_status,
            "metrics": rec.metrics,
            "created_at": rec.created_at,
            "notes": rec.notes,
        }
        self._save()
        return rec

    def transition_stage(self, model_id: str, version: str, new_stage: str) -> bool:
        """Transition model version stage (e.g. staging -> production)."""
        key = f"{model_id}:{version}"
        if key not in self.models:
            return False

        if new_stage == "production":
            # Demote current production model to rollback/archived
            for k, v in self.models.items():
                if v.get("model_id") == model_id and v.get("stage") == "production":
                    v["stage"] = "rollback"

        self.models[key]["stage"] = new_stage
        self.models[key]["approval_status"] = (
            "APPROVED"
            if new_stage == "production"
            else self.models[key]["approval_status"]
        )
        self._save()
        return True

    def list_models(self) -> list[dict[str, Any]]:
        """List all registered model versions."""
        return list(self.models.values())
