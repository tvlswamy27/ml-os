"""
Experiment Tracker Engine for ML-OS.

Automatically tracks every AutoML execution run, metrics, environment, artifacts, and parameters.

Author: Antigravity
License: MIT
"""

import json
import os
import platform
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ExperimentRecord:
    """Experiment execution record metadata."""

    experiment_id: str
    timestamp: str
    dataset_fingerprint: str
    problem_type: str
    pipeline_id: str
    selected_model: str
    candidate_models: list[str] = field(default_factory=list)
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    cv_scores: list[float] = field(default_factory=list)
    training_time_s: float = 0.0
    prediction_time_s: float = 0.0
    memory_usage_mb: float = 0.0
    feature_importance: dict[str, float] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    status: str = "SUCCESS"


from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from uuid import UUID


def _make_serializable(obj: Any) -> Any:
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _make_serializable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_make_serializable(x) for x in obj]
    return str(obj)


class DictAttributeWrapper(dict):
    """Helper enabling dot-notation attribute access, dict indexing, and isinstance(x, dict) for legacy test compatibility."""

    def __init__(self, d: Any):
        super().__init__()
        self._dict = d if isinstance(d, dict) else {}
        if isinstance(d, dict):
            for k, v in d.items():
                val = _make_serializable(v)
                wrapped_val = (
                    DictAttributeWrapper(val) if isinstance(val, dict) else val
                )
                self[k] = wrapped_val
                setattr(self, str(k), wrapped_val)

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        if name == "metrics":
            if "metrics" in self:
                return self["metrics"]
            return self
        return None


class ExperimentTracker:
    """
    Tracks and logs experiment execution metrics in .mlos/experiments/.
    """

    def __init__(self, workspace_root: Path | str = "."):
        self.workspace_root = Path(workspace_root)
        self.experiments_dir = self.workspace_root / ".mlos" / "experiments"
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_file = self.experiments_dir / "experiments.json"
        self._load()

    def _load(self) -> None:
        self.experiments: dict[str, dict[str, Any]] = {}
        if self.experiments_file.exists():
            try:
                self.experiments = json.loads(
                    self.experiments_file.read_text(encoding="utf-8")
                )
            except Exception:
                self.experiments = {}

    def _save(self) -> None:
        safe_data = _make_serializable(self.experiments)
        self.experiments_file.write_text(
            json.dumps(safe_data, indent=2), encoding="utf-8"
        )

    def log_experiment(
        self,
        dataset_fingerprint: str,
        problem_type: str,
        pipeline_id: str,
        selected_model: str,
        candidate_models: list[str],
        metrics: dict[str, float],
        cv_scores: list[float],
        training_time_s: float,
        prediction_time_s: float,
        memory_usage_mb: float,
        feature_importance: dict[str, float],
        artifacts: dict[str, str],
        hyperparameters: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> ExperimentRecord:
        """Log a new experiment run."""
        exp_id = experiment_id or str(uuid.uuid4())[:8]
        env_meta = {
            "python_version": sys.version.split()[0],
            "os": platform.platform(),
            "cpu_count": str(os.cpu_count()),
        }

        rec = ExperimentRecord(
            experiment_id=exp_id,
            timestamp=datetime.utcnow().isoformat(),
            dataset_fingerprint=dataset_fingerprint,
            problem_type=problem_type,
            pipeline_id=pipeline_id,
            selected_model=selected_model,
            candidate_models=candidate_models,
            hyperparameters=hyperparameters or {},
            metrics=metrics,
            cv_scores=cv_scores,
            training_time_s=training_time_s,
            prediction_time_s=prediction_time_s,
            memory_usage_mb=memory_usage_mb,
            feature_importance=feature_importance,
            artifacts=artifacts,
            environment=env_meta,
            status="SUCCESS",
        )

        if exp_id in self.experiments:
            # Merge!
            exp_data = self.experiments[exp_id]

            exp_data["dataset_fingerprint"] = rec.dataset_fingerprint
            exp_data["problem_type"] = rec.problem_type
            exp_data["pipeline_id"] = rec.pipeline_id
            exp_data["selected_model"] = rec.selected_model
            exp_data["candidate_models"] = rec.candidate_models
            exp_data["hyperparameters"] = rec.hyperparameters

            # Merge metrics
            existing_metrics = exp_data.get("metrics", {})
            exp_data["metrics"] = {**existing_metrics, **rec.metrics}

            exp_data["cv_scores"] = rec.cv_scores
            exp_data["training_time_s"] = rec.training_time_s
            exp_data["prediction_time_s"] = rec.prediction_time_s
            exp_data["memory_usage_mb"] = rec.memory_usage_mb
            exp_data["feature_importance"] = rec.feature_importance
            exp_data["artifacts"] = rec.artifacts
            exp_data["environment"] = rec.environment
            exp_data["status"] = rec.status
            exp_data["timestamp"] = rec.timestamp
        else:
            self.experiments[exp_id] = {
                "experiment_id": rec.experiment_id,
                "name": rec.experiment_id,
                "timestamp": rec.timestamp,
                "dataset_fingerprint": rec.dataset_fingerprint,
                "problem_type": rec.problem_type,
                "pipeline_id": rec.pipeline_id,
                "selected_model": rec.selected_model,
                "candidate_models": rec.candidate_models,
                "hyperparameters": rec.hyperparameters,
                "metrics": rec.metrics,
                "cv_scores": rec.cv_scores,
                "training_time_s": rec.training_time_s,
                "prediction_time_s": rec.prediction_time_s,
                "memory_usage_mb": rec.memory_usage_mb,
                "feature_importance": rec.feature_importance,
                "artifacts": rec.artifacts,
                "environment": rec.environment,
                "status": rec.status,
                "runs": [],
            }

        self._save()
        return rec

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        """Get experiment record by ID."""
        return self.experiments.get(experiment_id)

    def get_or_create_experiment(self, name: str) -> Any:
        """SDK compatibility helper returning an experiment container object."""

        class _LegacyExpContainer:
            def __init__(self, exp_id: str, name: str):
                self.experiment_id = exp_id
                self.name = name
                self.runs: list[Any] = []

        # 1. First, check if name is an exact experiment_id (key in self.experiments)
        if name in self.experiments:
            data = self.experiments[name]
            c = _LegacyExpContainer(name, data.get("name", name))
            c.runs = [
                DictAttributeWrapper(r) if isinstance(r, dict) else r
                for r in data.get("runs", [])
            ]
            return c

        # 2. Check if name looks like an explicit experiment_id (length 8 or UUID)
        is_explicit_id = False
        if len(name) == 8:
            try:
                int(name, 16)
                is_explicit_id = True
            except ValueError:
                pass

        if is_explicit_id:
            c = _LegacyExpContainer(name, name)
            return c

        # 3. For legacy calls (e.g. project name or model name)
        matches = []
        for exp_id, data in self.experiments.items():
            if (
                data.get("selected_model") == name
                or data.get("name") == name
                or exp_id == name
            ):
                matches.append((exp_id, data))

        if matches:
            matches = sorted(
                matches, key=lambda x: x[1].get("timestamp", ""), reverse=True
            )
            exp_id, data = matches[0]
            c = _LegacyExpContainer(exp_id, data.get("name", name))
            c.runs = [
                DictAttributeWrapper(r) if isinstance(r, dict) else r
                for r in data.get("runs", [])
            ]
            return c

        c = _LegacyExpContainer(name, name)
        return c

    def record_run(self, experiment_id: str, run_record: Any) -> None:
        """SDK compatibility helper for recording run objects."""
        run_data = _make_serializable(run_record)

        problem_type = None
        project_name = None
        if hasattr(run_record, "metadata") and isinstance(run_record.metadata, dict):
            problem_type = run_record.metadata.get("problem_type")
            project_name = run_record.metadata.get("project_name")
        if (
            not problem_type
            and isinstance(run_record, dict)
            and "metadata" in run_record
        ):
            problem_type = run_record["metadata"].get("problem_type")
            project_name = run_record["metadata"].get("project_name")

        run_metrics: dict[str, float] = {}
        if hasattr(run_record, "metrics") and run_record.metrics:
            run_metrics = getattr(run_record.metrics, "metrics", {})
        if not run_metrics and isinstance(run_record, dict) and "metrics" in run_record:
            run_metrics = run_record["metrics"].get("metrics", {})

        if experiment_id not in self.experiments:
            self.experiments[experiment_id] = {
                "experiment_id": str(experiment_id),
                "name": project_name or str(experiment_id),
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": run_metrics,
                "runs": [run_data],
            }
            if problem_type:
                self.experiments[experiment_id]["problem_type"] = problem_type
        else:
            exp_data = self.experiments[experiment_id]
            if "runs" not in exp_data:
                exp_data["runs"] = []
            exp_data["runs"].append(run_data)

            if project_name:
                exp_data["name"] = project_name
            if problem_type:
                exp_data["problem_type"] = problem_type

            existing_metrics = exp_data.get("metrics", {})
            exp_data["metrics"] = {**existing_metrics, **run_metrics}

        self._save()

    def list_experiments(self) -> list[dict[str, Any]]:
        """List all logged experiment records."""
        return list(self.experiments.values())
