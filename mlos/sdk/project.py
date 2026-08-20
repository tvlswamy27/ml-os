"""
MLProject main entry point SDK API.

Author: Antigravity
License: MIT
"""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    update_project_config_from_memory,
)
from mlos.communication.store import EventStore
from mlos.experiment.models import (
    KnowledgeSnapshot,
    Run,
    RunArtifact,
    RunEvent,
    RunExecution,
    RunMetrics,
)
from mlos.experiment.tracker import ExperimentTracker
from mlos.registry.artifact_registry import ArtifactRegistry, ExecutionArtifact


class MLProjectSession:
    """
    Session object returned by running an MLProject.
    """

    def __init__(self, run: Run, project: "MLProject") -> None:
        self.run = run
        self._project = project

    def get_evaluation_report(self) -> dict[str, Any]:
        """Fetch evaluation results summary from the session."""
        return {
            "status": self.run.execution.status,
            "metrics": self.run.metrics.metrics,
            "duration": self.run.execution.duration_seconds,
        }


class MLProject:
    """
    The only public entry point for ML-OS. Handles project configuration,
    version-controlled saving/loading, stage-based execution, and automatic lineage logging.
    """

    def __init__(
        self,
        dataset_path: str | None = None,
        target_column: str | None = None,
        project_path: str | None = None,
        name: str | None = None,
        goal: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.dataset_path: str | None = None
        self.target_column: str | None = None
        # Resolve project root using find_project_root
        found_root = find_project_root(project_path)
        if found_root:
            self.project_path = found_root
        elif project_path:
            self.project_path = Path(project_path).resolve()
        else:
            self.project_path = Path.cwd().resolve()

        self.project_path.mkdir(parents=True, exist_ok=True)
        self.memory = reconstruct_project_memory(self.project_path)

        if not self.memory:
            self.name = name or "DefaultProject"
            self.goal = goal or "OptimizationGoal"

            # Setup directories
            (self.project_path / ".mlos").mkdir(parents=True, exist_ok=True)

            from mlos.domain.services.project_memory_service import ProjectMemoryService

            memory_service = ProjectMemoryService()
            self.memory = memory_service.create(
                project_name=self.name,
                project_goal=self.goal,
            )
            update_project_config_from_memory(self.project_path, self.memory)
        else:
            self.name = self.memory.project_name
            self.goal = self.memory.project_goal

        # Override or set dataset paths
        if dataset_path:
            self.dataset_path = dataset_path
            from mlos.domain.models.dataset import Dataset

            old_problem_type = None
            if self.memory and self.memory.dataset:
                old_problem_type = self.memory.dataset.problem_type
            if not old_problem_type and self.memory and self.memory.project_profile:
                old_problem_type = self.memory.project_profile.problem_type

            self.memory.dataset = Dataset(
                path=dataset_path, target=target_column, problem_type=old_problem_type
            )
            update_project_config_from_memory(self.project_path, self.memory)
        else:
            self.dataset_path = (
                self.memory.dataset.path
                if (self.memory and self.memory.dataset)
                else None
            )

        self.target_column = target_column or (
            self.memory.dataset.target
            if (self.memory and self.memory.dataset)
            else None
        )

        # Extract problem_type from kwargs or manifest if provided
        problem_type_arg = kwargs.get("problem_type") or kwargs.get("task")
        if problem_type_arg and self.memory:
            from mlos.domain.models.project_profile import ProjectProfile

            if self.memory.project_profile is None:
                self.memory.project_profile = ProjectProfile(
                    problem_type=problem_type_arg.capitalize(),
                    complexity="low",
                    baseline_models=[],
                    risks=[],
                )
            else:
                self.memory.project_profile.problem_type = problem_type_arg.capitalize()
            update_project_config_from_memory(self.project_path, self.memory)

        # Initialize internal infrastructure registries (hidden from developer API)
        self.artifact_registry = ArtifactRegistry(str(self.project_path))
        self.experiment_tracker = ExperimentTracker(str(self.project_path))
        self.event_store = EventStore(str(self.project_path))

    @classmethod
    def load(cls, project_path: str) -> "MLProject":
        """
        Load an existing project workspace configuration transparently.
        """
        p = cls(project_path=project_path)
        return p

    def save(self) -> None:
        """
        Persist current workspace memory transparently to disk.
        """
        if self.memory:
            update_project_config_from_memory(self.project_path, self.memory)

    def run(self, experiment_id: str | None = None, run_id: str | None = None) -> MLProjectSession:
        """
        Execute the stage-based pipeline, auto-organizing outputs and logging lineage metrics.
        """
        assert self.memory is not None
        from mlos.engine.engine import MLOSEngine

        engine = MLOSEngine()
        engine.project_memory = self.memory
        engine.project_path = self.project_path

        # Use memory dataset path and target if not set on SDK facade
        dataset_path = self.dataset_path
        if not dataset_path and self.memory.dataset and self.memory.dataset.path:
            dataset_path = self.memory.dataset.path

        target_col = self.target_column
        if not target_col and self.memory.dataset and self.memory.dataset.target:
            target_col = self.memory.dataset.target

        run_record = engine.run_canonical_lifecycle(
            dataset_path=dataset_path or "",
            target_column=target_col,
            output_dir=str(self.project_path / "artifacts" / "automl"),
            experiment_id=experiment_id,
            run_id=run_id,
            workspace_root=self.project_path,
        )

        self.save()
        return MLProjectSession(run_record, self)

    def metrics(self) -> dict[str, float]:
        """Return the evaluation metrics associated with the last successful run."""
        self.experiment_tracker._load()
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        if not exp.runs:
            return {}
        return exp.runs[-1].metrics.metrics

    def artifacts(self) -> list[ExecutionArtifact]:
        """Retrieve list of all registered outputs inside the ArtifactRegistry."""
        self.artifact_registry.load()
        return self.artifact_registry.list_artifacts()

    def explain(self) -> dict[str, float]:
        """Fetch model explainability importance map."""
        import json

        self.artifact_registry.load()
        explain_art = self.artifact_registry.list_artifacts(
            artifact_type="EXPLAINABILITY"
        )
        if not explain_art:
            return {}
        path = self.project_path / explain_art[-1].file_path
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def graph(self) -> dict[str, Any]:
        """Fetch visual execution DAG layout details."""
        return {
            "nodes": [
                {"id": "Data Loading", "subsystem": "data_loader"},
                {"id": "Validation", "subsystem": "validator"},
                {"id": "Transformation", "subsystem": "transformer"},
                {"id": "Feature Engineering", "subsystem": "feature_intel"},
                {"id": "Training", "subsystem": "trainer"},
                {"id": "Hyperparameter Optimization", "subsystem": "hpo"},
                {"id": "Evaluation", "subsystem": "evaluator"},
                {"id": "Explainability", "subsystem": "explainer"},
                {"id": "Artifact Generation", "subsystem": "generator"},
                {"id": "Deployment Packaging", "subsystem": "packager"},
            ],
            "edges": [
                {"source": "Data Loading", "target": "Validation"},
                {"source": "Validation", "target": "Transformation"},
                {"source": "Transformation", "target": "Feature Engineering"},
                {"source": "Feature Engineering", "target": "Training"},
                {"source": "Training", "target": "Hyperparameter Optimization"},
                {"source": "Hyperparameter Optimization", "target": "Evaluation"},
                {"source": "Evaluation", "target": "Explainability"},
                {"source": "Explainability", "target": "Artifact Generation"},
                {"source": "Artifact Generation", "target": "Deployment Packaging"},
            ],
        }

    def history(self) -> list[dict[str, Any]]:
        """Return history metadata of all executed runs."""
        self.experiment_tracker._load()
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        return [
            {
                "run_id": str(getattr(r, "run_id", "")),
                "name": str(getattr(r, "name", "")),
                "timestamp": (
                    r.timestamp.isoformat()
                    if hasattr(r, "timestamp") and hasattr(r.timestamp, "isoformat")
                    else str(getattr(r, "timestamp", ""))
                ),
                "duration": getattr(
                    getattr(r, "execution", None), "duration_seconds", 0.0
                ),
                "metrics": getattr(
                    getattr(r, "metrics", None), "metrics", getattr(r, "metrics", {})
                ),
                "status": getattr(getattr(r, "execution", None), "status", "SUCCESS"),
            }
            for r in exp.runs
        ]

    def compare_runs(self) -> dict[str, dict[str, Any]]:
        """Compare evaluation metrics side-by-side across all historical runs."""
        self.experiment_tracker._load()
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        comparison = {}
        for r in exp.runs:
            run_name = str(getattr(r, "name", "run"))
            ts = (
                r.timestamp.isoformat()
                if hasattr(r, "timestamp") and hasattr(r.timestamp, "isoformat")
                else str(getattr(r, "timestamp", ""))
            )
            met = getattr(
                getattr(r, "metrics", None), "metrics", getattr(r, "metrics", {})
            )
            dur = getattr(getattr(r, "execution", None), "duration_seconds", 0.0)
            comparison[run_name] = {
                "timestamp": ts,
                "metrics": met,
                "duration": dur,
            }
        return comparison

    def export(self, export_path: str = "project_export.zip") -> str:
        """Compress the project artifacts and index logs as a zip archive."""
        zip_file_path = Path(export_path)
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            # Add files from the project workspace
            for folder in ("artifacts", ".mlos"):
                folder_path = self.project_path / folder
                if folder_path.exists():
                    for file_p in folder_path.rglob("*"):
                        if file_p.is_file():
                            zip_ref.write(file_p, file_p.relative_to(self.project_path))
        return str(zip_file_path.resolve())
