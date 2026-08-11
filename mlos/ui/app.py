"""
Flask backend app for ML-OS UI.
Serves static SPA and interacts with ML-OS core engines.
"""

import os
import sys
import uuid
import threadpoolctl
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Any, Dict

from flask import Flask, jsonify, request, render_template, send_from_directory

from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    save_project_config,
    update_project_config_from_memory,
)
from mlos.engine.engine import MLOSEngine
from mlos.sdk.project import MLProject
from mlos.experiment.tracker import ExperimentTracker
from mlos.experiment.comparator import ExperimentComparator

# Initialize Flask app
# Since template_folder and static_folder are inside mlos/ui/ templates and static
current_dir = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(current_dir / "templates"),
    static_folder=str(current_dir / "static"),
)

# Background execution state store
active_runs: Dict[str, Dict[str, Any]] = {}


def get_active_project_path() -> Path:
    """Find the active project root directory based on current working dir."""
    root = find_project_root()
    if root:
        return root
    return Path.cwd().resolve()


@app.route("/")
def index():
    """Serve the main SPA layout."""
    return render_template("index.html")


@app.route("/api/project", methods=["GET"])
def get_project():
    """Retrieve details of the currently loaded project."""
    try:
        project_root = get_active_project_path()
        has_dot_mlos = (project_root / ".mlos").is_dir()

        if not has_dot_mlos:
            return jsonify({"status": "no_project", "project_path": str(project_root)})

        memory = reconstruct_project_memory(project_root)
        if not memory:
            return jsonify(
                {
                    "status": "no_project",
                    "project_path": str(project_root),
                    "error": "Failed to load project config.",
                }
            )

        # Get latest experiment and model details if tracker has any
        tracker = ExperimentTracker(project_root)
        exps = tracker.list_experiments()
        latest_exp = None
        latest_model = None
        latest_metrics = {}
        model_stage = None

        if exps:
            # Sort by timestamp
            exps_sorted = sorted(
                exps, key=lambda e: e.get("timestamp", ""), reverse=True
            )
            latest_exp = exps_sorted[0].get("experiment_id")
            latest_model = exps_sorted[0].get("selected_model")
            latest_metrics = exps_sorted[0].get("metrics", {})

            # Retrieve model stage from registry if model registry exists
            from mlos.registry.model_registry import ModelRegistry

            try:
                model_reg = ModelRegistry(project_root)
                models = model_reg.list_models()
                if models:
                    # Match latest model
                    matching = [m for m in models if m.get("model_id") == latest_model]
                    if matching:
                        model_stage = matching[-1].get("stage")
            except Exception:
                pass

        profile_data = None
        if memory.project_profile:
            profile_data = {
                "problem_type": memory.project_profile.problem_type,
                "complexity": memory.project_profile.complexity,
                "baseline_models": list(memory.project_profile.baseline_models),
                "risks": list(memory.project_profile.risks),
                "decisions": [],
            }

        dataset_data = None
        if memory.dataset:
            dataset_data = {
                "path": memory.dataset.path,
                "rows": memory.dataset.rows,
                "columns": memory.dataset.columns,
                "target": memory.dataset.target,
                "problem_type": memory.dataset.problem_type,
                "duplicate_rows": memory.dataset.duplicate_rows,
                "missing_values_count": (
                    sum(memory.dataset.missing_values.values())
                    if memory.dataset.missing_values
                    else 0
                ),
            }

        return jsonify(
            {
                "status": "active",
                "project_name": memory.project_name,
                "project_goal": memory.project_goal,
                "project_path": str(project_root),
                "current_stage": memory.current_stage,
                "dataset": dataset_data,
                "profile": profile_data,
                "latest_experiment": latest_exp,
                "latest_model": latest_model,
                "model_stage": model_stage or "staging",
                "latest_metrics": latest_metrics,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/project/init", methods=["POST"])
def init_project():
    """Initialize a new ML-OS workspace."""
    try:
        data = request.json or {}
        name = data.get("name")
        goal = data.get("goal", "ML Optimization Goal")
        target_path = data.get("path")

        if not name:
            return jsonify({"error": "Project name is required"}), 400

        cwd = Path.cwd().resolve()
        if target_path:
            project_root = Path(target_path).resolve()
        else:
            project_root = cwd / name
            project_root = project_root.resolve()

        engine = MLOSEngine()
        # Create project folder
        project_root = engine.create_project(
            name=name, goal=goal, destination=project_root
        )

        # Save config yaml
        save_project_config(
            project_root,
            {
                "schema_version": "3.0.0",
                "project_name": name,
                "project_goal": goal,
                "current_stage": "Project Initialization",
                "completed_tasks": [],
                "notes": [],
            },
        )

        return jsonify(
            {
                "message": f"Successfully initialized project '{name}'",
                "project_path": str(project_root),
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to initialize project: {str(e)}"}), 500


@app.route("/api/project/analyze", methods=["POST"])
def analyze_dataset():
    """Run analysis on a dataset."""
    try:
        data = request.json or {}
        dataset_path = data.get("dataset_path")
        target_column = data.get("target_column")

        if not dataset_path:
            return jsonify({"error": "Dataset path is required"}), 400

        project_root = get_active_project_path()
        if not (project_root / ".mlos").is_dir():
            return (
                jsonify(
                    {"error": "No project initialized. Initialize a project first."}
                ),
                400,
            )

        memory = reconstruct_project_memory(project_root)
        if not memory:
            return jsonify({"error": "Failed to load project config."}), 400

        # Run analysis using engine
        engine = MLOSEngine()
        engine.project_memory = memory

        # Resolve path
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_root / dataset_path).resolve()

        if not path_resolved.exists():
            return (
                jsonify({"error": f"Dataset file does not exist at: {path_resolved}"}),
                400,
            )

        report = engine.run_analysis(str(path_resolved), target_column)

        # Save memory state
        update_project_config_from_memory(project_root, engine.project_memory)

        # Prepare JSON response
        dataset = report.dataset

        # Format decisions
        decisions_list = []
        for dec in report.decisions:
            decisions_list.append(
                {
                    "title": dec.title,
                    "strategy": dec.strategy,
                    "confidence": dec.confidence,
                    "reason": dec.reason,
                }
            )

        # Format recommendations
        recs_list = []
        for rec in report.recommendations:
            recs_list.append(
                {
                    "priority": rec.priority.value,
                    "title": rec.title,
                    "description": rec.description,
                }
            )

        return jsonify(
            {
                "dataset_summary": {
                    "path": str(dataset.path),
                    "rows": dataset.rows,
                    "columns": dataset.columns,
                    "target": dataset.target or "None",
                    "problem_type": dataset.problem_type or "Unknown",
                    "duplicate_rows": dataset.duplicate_rows,
                    "missing_values": (
                        dict(dataset.missing_values) if dataset.missing_values else {}
                    ),
                },
                "features": {
                    "numerical": list(dataset.numerical_columns),
                    "categorical": list(dataset.categorical_columns),
                },
                "problem_intelligence": {
                    "problem_type": dataset.problem_type or "Classification",
                    "complexity": (
                        memory.project_profile.complexity
                        if memory.project_profile
                        else "low"
                    ),
                    "baseline_models": (
                        list(memory.project_profile.baseline_models)
                        if memory.project_profile
                        else []
                    ),
                    "risks": (
                        list(memory.project_profile.risks)
                        if memory.project_profile
                        else []
                    ),
                    "decisions": decisions_list,
                    "recommendations": recs_list,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to analyze dataset: {str(e)}"}), 500


def background_run_pipeline(
    run_id: str, project_root: Path, dataset_path: str, target_column: str
):
    """Executes the pipeline run in a background thread and updates progress state."""
    active_runs[run_id] = {
        "status": "running",
        "current_stage": "Analysis",
        "completed_stages": [],
        "error": None,
    }

    stages = [
        "Analysis",
        "Feature Intelligence",
        "Meta Reasoning",
        "Planning",
        "Execution Runtime",
        "Training",
        "Evaluation",
        "Explainability",
        "Artifacts Generation",
        "Experiment Tracking",
        "Knowledge Capture",
    ]

    try:
        # Resolve absolute dataset path
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_root / dataset_path).resolve()

        if not path_resolved.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {path_resolved}")

        # 1. Initialize MLProject
        project = MLProject(
            dataset_path=str(path_resolved),
            target_column=target_column,
            project_path=str(project_root),
        )

        engine = MLOSEngine()
        # Wire memory
        engine.project_memory = project.memory

        # Let's execute the graph topological run. We will update stages dynamically as it runs.
        # Since project.run() executes all stages sequentially inside one function,
        # we will run it, but mock stage-by-stage progression updates to the UI,
        # because the internal execution runtime is synchronous and fast in this ML-OS version.

        # Step-by-step progress updating helper
        def update_progress(current_stage_name: str, completed_list: list):
            active_runs[run_id]["current_stage"] = current_stage_name
            active_runs[run_id]["completed_stages"] = completed_list

        # Simulate quick progression to show the UI timeline updating
        update_progress("Analysis", [])
        import time

        time.sleep(0.5)

        update_progress("Feature Intelligence", ["Analysis"])
        time.sleep(0.5)

        update_progress("Meta Reasoning", ["Analysis", "Feature Intelligence"])
        time.sleep(0.5)

        update_progress(
            "Planning", ["Analysis", "Feature Intelligence", "Meta Reasoning"]
        )
        time.sleep(0.5)

        from mlos.experiment.ids import generate_experiment_id

        generated_exp_id = generate_experiment_id()

        # Run SDK workflow stages now
        update_progress(
            "Execution Runtime",
            ["Analysis", "Feature Intelligence", "Meta Reasoning", "Planning"],
        )
        session = project.run(experiment_id=generated_exp_id)
        time.sleep(0.5)

        update_progress(
            "Training",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
            ],
        )
        # Run AutoML search
        results, artifacts = engine.run_automl(
            str(path_resolved),
            target_column=target_column,
            output_dir=str(project_root / "artifacts" / "automl"),
            experiment_id=generated_exp_id,
            workspace_root=project_root,
        )
        time.sleep(0.5)

        update_progress(
            "Evaluation",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
                "Training",
            ],
        )
        time.sleep(0.5)

        update_progress(
            "Explainability",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
                "Training",
                "Evaluation",
            ],
        )
        time.sleep(0.5)

        update_progress(
            "Artifacts Generation",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
                "Training",
                "Evaluation",
                "Explainability",
            ],
        )
        time.sleep(0.5)

        update_progress(
            "Experiment Tracking",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
                "Training",
                "Evaluation",
                "Explainability",
                "Artifacts Generation",
            ],
        )
        time.sleep(0.5)

        update_progress(
            "Knowledge Capture",
            [
                "Analysis",
                "Feature Intelligence",
                "Meta Reasoning",
                "Planning",
                "Execution Runtime",
                "Training",
                "Evaluation",
                "Explainability",
                "Artifacts Generation",
                "Experiment Tracking",
            ],
        )
        time.sleep(0.5)

        # Final success details
        eval_metrics = project.metrics()

        # Load the latest experiment details from tracker to get correct experiment ID
        tracker = ExperimentTracker(project_root)
        exps = tracker.list_experiments()
        experiment_id = session.run.experiment_id
        if exps:
            # Match latest
            latest_rec = sorted(
                exps, key=lambda e: e.get("timestamp", ""), reverse=True
            )[0]
            experiment_id = latest_rec.get("experiment_id", experiment_id)
            eval_metrics = latest_rec.get("metrics", eval_metrics)

        active_runs[run_id] = {
            "status": "success",
            "current_stage": None,
            "completed_stages": stages,
            "experiment_id": str(experiment_id),
            "problem_type": (
                project.memory.project_profile.problem_type
                if (project.memory and project.memory.project_profile)
                else "Classification"
            ),
            "execution_time_s": session.run.execution.duration_seconds,
            "artifacts_count": len(project.artifacts()),
            "metrics": eval_metrics,
            "error": None,
        }

    except Exception as e:
        import traceback

        print(f"Pipeline background execution error: {e}", file=sys.stderr)
        traceback.print_exc()
        active_runs[run_id] = {
            "status": "failed",
            "current_stage": None,
            "completed_stages": [],
            "error": str(e),
        }


@app.route("/api/project/run", methods=["POST"])
def run_pipeline():
    """Start background ML pipeline execution."""
    try:
        data = request.json or {}
        dataset_path = data.get("dataset_path")
        target_column = data.get("target_column")

        if not dataset_path:
            return jsonify({"error": "Dataset path is required"}), 400

        project_root = get_active_project_path()
        if not (project_root / ".mlos").is_dir():
            return (
                jsonify(
                    {"error": "No project initialized. Initialize a project first."}
                ),
                400,
            )

        run_id = str(uuid.uuid4())

        # Start execution in a background thread
        thread = Thread(
            target=background_run_pipeline,
            args=(run_id, project_root, dataset_path, target_column),
        )
        thread.start()

        return jsonify(
            {"run_id": run_id, "message": "ML Pipeline started successfully"}
        )

    except Exception as e:
        return jsonify({"error": f"Failed to start pipeline: {str(e)}"}), 500


@app.route("/api/project/run/status/<run_id>", methods=["GET"])
def get_run_status(run_id):
    """Poll the status of an active pipeline execution."""
    if run_id not in active_runs:
        return jsonify({"error": "Run ID not found"}), 404
    return jsonify(active_runs[run_id])


@app.route("/api/experiments", methods=["GET"])
def list_experiments():
    """List all experiments tracked in this project."""
    try:
        project_root = get_active_project_path()
        tracker = ExperimentTracker(project_root)
        experiments = tracker.list_experiments()

        # Sort by timestamp descending
        experiments = sorted(
            experiments, key=lambda e: e.get("timestamp", ""), reverse=True
        )

        return jsonify(experiments)
    except Exception as e:
        return jsonify({"error": f"Failed to list experiments: {str(e)}"}), 500


@app.route("/api/experiments/<experiment_id>", methods=["GET"])
def get_experiment_details(experiment_id):
    """Retrieve details for a specific experiment run."""
    try:
        project_root = get_active_project_path()
        tracker = ExperimentTracker(project_root)
        exp = tracker.get_experiment(experiment_id)

        if not exp:
            return jsonify({"error": f"Experiment '{experiment_id}' not found"}), 404

        return jsonify(exp)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch experiment details: {str(e)}"}), 500


@app.route("/api/experiments/compare", methods=["POST"])
def compare_experiments():
    """Compare two experiments side-by-side using the ExperimentComparator."""
    try:
        data = request.json or {}
        exp1_id = data.get("exp1")
        exp2_id = data.get("exp2")

        if not exp1_id or not exp2_id:
            return (
                jsonify(
                    {"error": "Both exp1 and exp2 IDs are required for comparison"}
                ),
                400,
            )

        project_root = get_active_project_path()
        tracker = ExperimentTracker(project_root)

        comparator = ExperimentComparator(tracker)
        diff = comparator.compare_experiments(exp1_id, exp2_id)

        return jsonify(diff)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to compare experiments: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
