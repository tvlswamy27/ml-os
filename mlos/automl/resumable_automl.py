"""
Resumable AutoML Manager for ML-OS.

Resumes interrupted AutoML runs from checkpointed stages.

Author: Antigravity
License: MIT
"""

from pathlib import Path

from mlos.cache.cache_engine import CacheEngine
from mlos.domain.models.model_result import ModelResult


class ResumableAutoMLManager:
    """
    Checkpoints and restores completed model evaluations for resumable AutoML execution.
    """

    def __init__(self, workspace_root: Path | str = "."):
        self.cache_engine = CacheEngine(workspace_root)

    def get_completed_models(self, dataset_fingerprint: str) -> dict[str, ModelResult]:
        """Get already completed model results for a dataset fingerprint."""
        cached = self.cache_engine.get(f"checkpoint_{dataset_fingerprint}")
        return cached if isinstance(cached, dict) else {}

    def checkpoint_model_result(
        self, dataset_fingerprint: str, model_id: str, result: ModelResult
    ) -> None:
        """Checkpoint a completed model evaluation."""
        completed = self.get_completed_models(dataset_fingerprint)
        completed[model_id] = result
        self.cache_engine.set(f"checkpoint_{dataset_fingerprint}", completed)
