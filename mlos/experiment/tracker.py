"""
ExperimentTracker orchestrating experiment metadata, runs, metrics, and snapshots.

Author: Antigravity
License: MIT
"""

import yaml
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, List, Optional
from mlos.experiment.models import (
    Experiment,
    Run,
    RunExecution,
    RunMetrics,
    RunArtifact,
    RunEvent,
    KnowledgeSnapshot,
)


class ExperimentTracker:
    """
    Service tracking running experiments and managing execution histories.
    """

    def __init__(self, project_path: str) -> None:
        self.project_path = Path(project_path)
        self.experiments_file = self.project_path / ".mlos" / "experiments.yaml"
        self._experiments: Dict[str, Experiment] = {}
        self.load()

    def get_or_create_experiment(self, name: str) -> Experiment:
        """Fetch an existing experiment by name or initialize a new one."""
        for exp in self._experiments.values():
            if exp.name == name:
                return exp

        exp = Experiment(
            experiment_id=uuid4(),
            name=name,
            created_at=datetime.now(),
            runs=[],
        )
        self._experiments[str(exp.experiment_id)] = exp
        self.save()
        return exp

    def record_run(self, experiment_id: UUID, run: Run) -> None:
        """Record an execution run under an active experiment."""
        exp = self._experiments.get(str(experiment_id))
        if not exp:
            raise ValueError(f"Experiment with ID '{experiment_id}' does not exist.")

        # Reconstruct experiment to append new run since it's frozen
        updated_runs = list(exp.runs) + [run]
        updated_exp = Experiment(
            experiment_id=exp.experiment_id,
            name=exp.name,
            created_at=exp.created_at,
            runs=updated_runs,
        )
        self._experiments[str(experiment_id)] = updated_exp
        self.save()

    def list_experiments(self) -> List[Experiment]:
        """List all tracked experiments."""
        return list(self._experiments.values())

    def get_run(self, run_id: UUID) -> Optional[Run]:
        """Retrieve a specific run by ID."""
        for exp in self._experiments.values():
            for run in exp.runs:
                if run.run_id == run_id:
                    return run
        return None

    def save(self) -> None:
        """Persist experiments tracker metadata to YAML file."""
        self.experiments_file.parent.mkdir(parents=True, exist_ok=True)
        serialized: Dict[str, Any] = {}
        for exp_id, exp in self._experiments.items():
            runs_list = []
            for run in exp.runs:
                runs_list.append(
                    {
                        "run_id": str(run.run_id),
                        "experiment_id": str(run.experiment_id),
                        "name": run.name,
                        "timestamp": run.timestamp.isoformat(),
                        "execution": {
                            "execution_id": str(run.execution.execution_id),
                            "status": run.execution.status,
                            "start_time": run.execution.start_time.isoformat(),
                            "end_time": run.execution.end_time.isoformat(),
                            "duration_seconds": run.execution.duration_seconds,
                            "stdout": run.execution.stdout,
                            "stderr": run.execution.stderr,
                            "exit_code": run.execution.exit_code,
                            "pipeline_hash": run.execution.pipeline_hash,
                        },
                        "metrics": {
                            "metrics_id": str(run.metrics.metrics_id),
                            "metrics": run.metrics.metrics,
                            "timestamp": run.metrics.timestamp.isoformat(),
                        },
                        "artifacts": [
                            {
                                "artifact_id": str(a.artifact_id),
                                "name": a.name,
                                "artifact_type": a.artifact_type,
                                "file_path": a.file_path,
                                "version": a.version,
                            }
                            for a in run.artifacts
                        ],
                        "events": [
                            {
                                "event_id": str(ev.event_id),
                                "event_type": ev.event_type,
                                "timestamp": ev.timestamp.isoformat(),
                                "source": ev.source,
                                "payload": ev.payload,
                            }
                            for ev in run.events
                        ],
                        "knowledge_snapshot": {
                            "snapshot_id": str(run.knowledge_snapshot.snapshot_id),
                            "timestamp": run.knowledge_snapshot.timestamp.isoformat(),
                            "active_rules_count": run.knowledge_snapshot.active_rules_count,
                            "rules": run.knowledge_snapshot.rules,
                        },
                        "metadata": run.metadata,
                    }
                )
            serialized[exp_id] = {
                "experiment_id": str(exp.experiment_id),
                "name": exp.name,
                "created_at": exp.created_at.isoformat(),
                "runs": runs_list,
            }
        with open(self.experiments_file, "w") as f:
            yaml.safe_dump(serialized, f, sort_keys=False)

    def load(self) -> None:
        """Load experiment runs from disk."""
        if not self.experiments_file.exists():
            return
        try:
            with open(self.experiments_file, "r") as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return

            for exp_id, exp_data in data.items():
                runs = []
                for rd in exp_data.get("runs", []):
                    exec_d = rd["execution"]
                    execution = RunExecution(
                        execution_id=UUID(exec_d["execution_id"]),
                        status=exec_d["status"],
                        start_time=datetime.fromisoformat(exec_d["start_time"]),
                        end_time=datetime.fromisoformat(exec_d["end_time"]),
                        duration_seconds=float(exec_d["duration_seconds"]),
                        stdout=exec_d["stdout"],
                        stderr=exec_d["stderr"],
                        exit_code=int(exec_d["exit_code"]),
                        pipeline_hash=exec_d.get("pipeline_hash"),
                    )

                    met_d = rd["metrics"]
                    metrics = RunMetrics(
                        metrics_id=UUID(met_d["metrics_id"]),
                        metrics=met_d["metrics"],
                        timestamp=datetime.fromisoformat(met_d["timestamp"]),
                    )

                    artifacts = [
                        RunArtifact(
                            artifact_id=UUID(ad["artifact_id"]),
                            name=ad["name"],
                            artifact_type=ad["artifact_type"],
                            file_path=ad["file_path"],
                            version=ad["version"],
                        )
                        for ad in rd.get("artifacts", [])
                    ]

                    events = [
                        RunEvent(
                            event_id=UUID(ev["event_id"]),
                            event_type=ev["event_type"],
                            timestamp=datetime.fromisoformat(ev["timestamp"]),
                            source=ev["source"],
                            payload=ev["payload"],
                        )
                        for ev in rd.get("events", [])
                    ]

                    snap_d = rd["knowledge_snapshot"]
                    snapshot = KnowledgeSnapshot(
                        snapshot_id=UUID(snap_d["snapshot_id"]),
                        timestamp=datetime.fromisoformat(snap_d["timestamp"]),
                        active_rules_count=int(snap_d["active_rules_count"]),
                        rules=snap_d.get("rules", []),
                    )

                    run = Run(
                        run_id=UUID(rd["run_id"]),
                        experiment_id=UUID(rd["experiment_id"]),
                        name=rd["name"],
                        timestamp=datetime.fromisoformat(rd["timestamp"]),
                        execution=execution,
                        metrics=metrics,
                        artifacts=artifacts,
                        events=events,
                        knowledge_snapshot=snapshot,
                        metadata=rd.get("metadata", {}),
                    )
                    runs.append(run)

                exp = Experiment(
                    experiment_id=UUID(exp_data["experiment_id"]),
                    name=exp_data["name"],
                    created_at=datetime.fromisoformat(exp_data["created_at"]),
                    runs=runs,
                )
                self._experiments[exp_id] = exp
        except Exception:
            pass
