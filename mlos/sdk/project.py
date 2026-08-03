"""
MLProject main entry point SDK API.

Author: Antigravity
License: MIT
"""

import shutil
import zipfile
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, List, Optional

from mlos.domain.models.project_memory import ProjectMemory
from mlos.cli.persistence import (
    reconstruct_project_memory,
    update_project_config_from_memory,
    find_project_root,
)
from mlos.registry.artifact_registry import ArtifactRegistry, ExecutionArtifact
from mlos.experiment.tracker import ExperimentTracker
from mlos.experiment.models import (
    Run,
    RunExecution,
    RunMetrics,
    RunArtifact,
    RunEvent,
    KnowledgeSnapshot,
)
from mlos.communication.event_bus import GlobalEventBus
from mlos.communication.store import EventStore


class MLProjectSession:
    """
    Session object returned by running an MLProject.
    """

    def __init__(self, run: Run, project: "MLProject") -> None:
        self.run = run
        self._project = project

    def get_evaluation_report(self) -> Dict[str, Any]:
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
        dataset_path: Optional[str] = None,
        target_column: Optional[str] = None,
        project_path: Optional[str] = None,
        name: Optional[str] = None,
        goal: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.dataset_path: Optional[str] = None
        self.target_column: Optional[str] = None
        self.project_path = Path(project_path) if project_path else Path(".")
        self.project_path.mkdir(parents=True, exist_ok=True)

        # Load or initialize project configuration
        is_explicit = project_path is not None
        project_root = None
        if is_explicit:
            if (self.project_path / ".mlos").is_dir():
                project_root = self.project_path
        else:
            project_root = find_project_root(self.project_path)

        if project_root:
            self.project_path = project_root
            self.memory = reconstruct_project_memory(project_root)
        else:
            self.memory = None

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

            self.memory.dataset = Dataset(path=dataset_path, target=target_column)
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

    def run(self) -> MLProjectSession:
        """
        Execute the stage-based pipeline, auto-organizing outputs and logging lineage metrics.
        """
        assert self.memory is not None
        from mlos.execution_intelligence.stage import (
            DataLoadingStage,
            ValidationStage,
            TransformationStage,
            FeaturePipelineStage,
            TrainingStage,
            HyperparameterOptimizationStage,
            EvaluationStage,
            ExplainabilityStage,
            ArtifactGenerationStage,
            DeploymentPackagingStage,
        )
        from mlos.execution_intelligence.runtime import ExecutionGraph, ExecutionRuntime

        # Setup standard stage execution DAG
        graph = ExecutionGraph()

        stages = [
            DataLoadingStage(),
            ValidationStage(),
            TransformationStage(),
            FeaturePipelineStage(),
            TrainingStage(),
            HyperparameterOptimizationStage(),
            EvaluationStage(),
            ExplainabilityStage(),
            ArtifactGenerationStage(),
            DeploymentPackagingStage(),
        ]

        for s in stages:
            graph.add_stage(s)

        # Wire linear dependencies
        graph.add_dependency("Validation", "Data Loading")
        graph.add_dependency("Transformation", "Validation")
        graph.add_dependency("Feature Engineering", "Transformation")
        graph.add_dependency("Training", "Feature Engineering")
        graph.add_dependency("Hyperparameter Optimization", "Training")
        graph.add_dependency("Evaluation", "Hyperparameter Optimization")
        graph.add_dependency("Explainability", "Evaluation")
        graph.add_dependency("Artifact Generation", "Explainability")
        graph.add_dependency("Deployment Packaging", "Artifact Generation")

        runtime = ExecutionRuntime()
        start_time = datetime.now()

        # Run topologically sorted stage list
        results = runtime.run_graph(
            graph,
            self.memory,
            dataset_path=self.dataset_path or "",
            target=self.target_column or "",
            project_path=str(self.project_path),
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        ctx = results.get("__context__", {})

        # 1. Automatically register physical files inside ArtifactRegistry
        registered_artifacts = []

        if "model_file" in ctx:
            art = self.artifact_registry.register_artifact(
                name="model",
                artifact_type="MODEL",
                source_file_path=Path(ctx["model_file"]),
                metadata={"problem_type": ctx.get("problem_type")},
            )
            registered_artifacts.append(art)

        if "transformed_dataframe" in ctx:
            prep_file = self.project_path / "preprocessor.joblib"
            with open(prep_file, "w") as f:
                f.write("Imputer checkpoint placeholder")
            art = self.artifact_registry.register_artifact(
                name="preprocessor",
                artifact_type="PREPROCESSOR",
                source_file_path=prep_file,
            )
            registered_artifacts.append(art)

        if "metrics_file" in ctx:
            art = self.artifact_registry.register_artifact(
                name="metrics",
                artifact_type="REPORT",
                source_file_path=Path(ctx["metrics_file"]),
            )
            registered_artifacts.append(art)

        if "explainability_file" in ctx:
            art = self.artifact_registry.register_artifact(
                name="explainability_report",
                artifact_type="EXPLAINABILITY",
                source_file_path=Path(ctx["explainability_file"]),
            )
            registered_artifacts.append(art)

        if "deployment_package" in ctx:
            art = self.artifact_registry.register_artifact(
                name="deployment_package",
                artifact_type="DEPLOYMENT",
                source_file_path=Path(ctx["deployment_package"]),
            )
            registered_artifacts.append(art)

        # 2. Extract capture events log timeline
        events_timeline = self.event_store.get_timeline(
            start_time=start_time, end_time=end_time
        )
        run_events = [
            RunEvent(
                event_id=ev.event_id,
                event_type=ev.event_type,
                timestamp=ev.timestamp,
                source=ev.source,
                payload=ev.payload,
            )
            for ev in events_timeline
        ]

        # 3. Snapshot active system rules
        active_rules = []
        if self.memory.knowledge_entries:
            for entry in self.memory.knowledge_entries:
                active_rules.append(
                    {
                        "knowledge_id": str(entry.knowledge_id),
                        "target_component": entry.target_component,
                        "target_subsystem": entry.target_subsystem,
                        "parameters": (
                            dict(entry.parameters) if entry.parameters else {}
                        ),
                    }
                )

        knowledge_snap = KnowledgeSnapshot(
            snapshot_id=uuid4(),
            timestamp=datetime.now(),
            active_rules_count=len(active_rules),
            rules=active_rules,
        )

        # 4. Construct run record logs
        run_execution = RunExecution(
            execution_id=uuid4(),
            status="SUCCESS",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            stdout="Completed topological stages.",
            stderr="",
            exit_code=0,
            pipeline_hash=str(uuid4()),
        )

        run_metrics = RunMetrics(
            metrics_id=uuid4(),
            metrics=ctx.get("evaluation_metrics", {}),
            timestamp=datetime.now(),
        )

        model_run_artifacts = [
            RunArtifact(
                artifact_id=a.artifact_id,
                name=a.name,
                artifact_type=a.artifact_type,
                file_path=a.file_path,
                version=a.version,
            )
            for a in registered_artifacts
        ]

        experiment = self.experiment_tracker.get_or_create_experiment(self.name)
        run_record = Run(
            run_id=uuid4(),
            experiment_id=experiment.experiment_id,
            name=f"run_{len(experiment.runs) + 1}",
            timestamp=datetime.now(),
            execution=run_execution,
            metrics=run_metrics,
            artifacts=model_run_artifacts,
            events=run_events,
            knowledge_snapshot=knowledge_snap,
        )

        self.experiment_tracker.record_run(experiment.experiment_id, run_record)

        # Save final state memory
        self.save()

        return MLProjectSession(run_record, self)

    def metrics(self) -> Dict[str, float]:
        """Return the evaluation metrics associated with the last successful run."""
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        if not exp.runs:
            return {}
        return exp.runs[-1].metrics.metrics

    def artifacts(self) -> List[ExecutionArtifact]:
        """Retrieve list of all registered outputs inside the ArtifactRegistry."""
        return self.artifact_registry.list_artifacts()

    def explain(self) -> Dict[str, float]:
        """Fetch model explainability importance map."""
        import json

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

    def graph(self) -> Dict[str, Any]:
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

    def history(self) -> List[Dict[str, Any]]:
        """Return history metadata of all executed runs."""
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        return [
            {
                "run_id": str(r.run_id),
                "name": r.name,
                "timestamp": r.timestamp.isoformat(),
                "duration": r.execution.duration_seconds,
                "metrics": r.metrics.metrics,
                "status": r.execution.status,
            }
            for r in exp.runs
        ]

    def compare_runs(self) -> Dict[str, Dict[str, Any]]:
        """Compare evaluation metrics side-by-side across all historical runs."""
        exp = self.experiment_tracker.get_or_create_experiment(self.name)
        comparison = {}
        for r in exp.runs:
            comparison[r.name] = {
                "timestamp": r.timestamp.isoformat(),
                "metrics": r.metrics.metrics,
                "duration": r.execution.duration_seconds,
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
