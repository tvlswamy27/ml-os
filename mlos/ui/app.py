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
from threading import Thread, Lock
from typing import Any, Dict

from flask import Flask, jsonify, request, render_template, send_from_directory
from werkzeug.exceptions import HTTPException, BadRequest, UnsupportedMediaType
import pandas as pd

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
active_runs_lock = Lock()


def get_active_project_path() -> Path:
    """Find the active project root directory based on persistent pointer or cwd."""
    pointer_file = Path.home() / ".mlos_active_project"
    if pointer_file.is_file():
        try:
            persisted_path = Path(pointer_file.read_text(encoding="utf-8").strip()).resolve()
            if persisted_path.exists() and (persisted_path / ".mlos").is_dir():
                return persisted_path
        except Exception:
            pass
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
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to retrieve project details: {str(e)}"
            }
        }), 500


@app.route("/api/project/init", methods=["POST"])
def init_project():
    """Initialize a new ML-OS workspace."""
    try:
        if request.content_length and request.content_length > 0 and not request.is_json:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Content-Type must be application/json"
                }
            }), 415

        try:
            data = request.get_json() or {}
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must contain valid JSON."
                }
            }), 400

        name = data.get("name")
        goal = data.get("goal", "ML Optimization Goal")
        target_path = data.get("path")

        if not name:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Project name is required"
                }
            }), 400

        cwd = Path.cwd().resolve()
        if target_path:
            try:
                project_root = Path(target_path).resolve()
            except Exception as pe:
                return jsonify({
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": f"Invalid project path: {str(pe)}"
                    }
                }), 400
        else:
            project_root = cwd / name
            project_root = project_root.resolve()

        engine = MLOSEngine()
        # Create project folder
        try:
            project_root = engine.create_project(
                name=name, goal=goal, destination=project_root
            )
        except (OSError, ValueError) as pe:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": f"Invalid project path: {str(pe)}"
                }
            }), 400

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

        # Save active project pointer
        pointer_file = Path.home() / ".mlos_active_project"
        pointer_file.parent.mkdir(parents=True, exist_ok=True)
        pointer_file.write_text(str(project_root), encoding="utf-8")

        return jsonify(
            {
                "message": f"Successfully initialized project '{name}'",
                "project_path": str(project_root),
            }
        )

    except Exception as e:
        return jsonify({
            "error": {
                "code": "PROJECT_INITIALIZATION_FAILED",
                "message": f"Failed to initialize project: {str(e)}"
            }
        }), 500


@app.route("/api/project/analyze", methods=["POST"])
def analyze_dataset():
    """Run analysis on a dataset."""
    try:
        if request.content_length and request.content_length > 0 and not request.is_json:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Content-Type must be application/json"
                }
            }), 415

        try:
            data = request.get_json() or {}
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must contain valid JSON."
                }
            }), 400

        dataset_path = data.get("dataset_path")
        target_column = data.get("target_column")

        if not dataset_path:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset path is required"
                }
            }), 400

        project_root = get_active_project_path()
        if not (project_root / ".mlos").is_dir():
            return jsonify({
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "No project initialized. Initialize a project first."
                }
            }), 400

        # Resolve path
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_root / dataset_path).resolve()

        # Workspace isolation traversal check
        try:
            path_resolved.relative_to(project_root)
        except ValueError:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset outside workspace"
                }
            }), 400

        if not path_resolved.exists():
            return jsonify({
                "error": {
                    "code": "DATASET_NOT_FOUND",
                    "message": f"Dataset file does not exist at: {path_resolved}"
                }
            }), 404

        # Verify dataset format
        suffix = path_resolved.suffix.lower()
        if suffix not in [".csv", ".parquet"]:
            return jsonify({
                "error": {
                    "code": "DATASET_INVALID",
                    "message": "Unsupported file type. Only CSV and Parquet are supported."
                }
            }), 400

        try:
            if suffix == ".csv":
                df_temp = pd.read_csv(path_resolved, nrows=2)
            else:
                df_temp = pd.read_parquet(path_resolved)

            if target_column and target_column not in df_temp.columns:
                return jsonify({
                    "error": {
                        "code": "TARGET_NOT_FOUND",
                        "message": f"Target column '{target_column}' not found in dataset."
                    }
                }), 400
        except Exception as read_err:
            return jsonify({
                "error": {
                    "code": "DATASET_INVALID",
                    "message": f"Failed to read dataset: {str(read_err)}"
                }
            }), 400

        memory = reconstruct_project_memory(project_root)
        if not memory:
            return jsonify({
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to load project config."
                }
            }), 500

        # Run analysis using engine
        engine = MLOSEngine()
        engine.project_memory = memory

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
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to analyze dataset: {str(e)}"
            }
        }), 500


def background_run_pipeline(
    run_id: str, project_root: Path, dataset_path: str, target_column: str
):
    """Executes the pipeline run in a background thread and updates progress state based on events."""
    from mlos.communication.event_bus import GlobalEventBus
    from mlos.execution.exceptions import ExecutionCancelledError

    event_bus = GlobalEventBus()

    # Event listener function
    def on_event(event):
        if event.run_id != run_id and event.payload.get("run_id") != run_id:
            return

        with active_runs_lock:
            if run_id not in active_runs:
                return
            
            run_info = active_runs[run_id]
            # Prevent overwriting terminal state
            if run_info.get("status") in ("completed", "failed", "cancelled"):
                return

            if event.event_type == "ExecutionStarted":
                if run_info.get("status") == "queued":
                    run_info["status"] = "running"
            elif event.event_type == "StageStarted":
                stage_name = event.payload.get("stage")
                run_info["current_stage"] = stage_name
            elif event.event_type == "StageCompleted":
                stage_name = event.payload.get("stage")
                if stage_name not in run_info["completed_stages"]:
                    run_info["completed_stages"].append(stage_name)
            elif event.event_type == "StageFailed":
                stage_name = event.payload.get("stage")
                run_info["failed_stage"] = stage_name

    event_bus.subscribe("*", on_event)

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
        engine.project_memory = project.memory

        from mlos.experiment.ids import generate_experiment_id
        generated_exp_id = generate_experiment_id()

        # Check cooperative cancellation before starting Project.run
        if event_bus.is_cancel_requested(run_id):
            raise ExecutionCancelledError("Run cancelled before starting ExecutionRuntime.")

        # Run SDK workflow stages (this executes both ML stages and AutoML Search canonically)
        session = project.run(experiment_id=generated_exp_id, run_id=run_id)

        # Final success details
        eval_metrics = project.metrics()

        tracker = ExperimentTracker(project_root)
        exps = tracker.list_experiments()
        experiment_id = session.run.experiment_id
        if exps:
            latest_rec = sorted(
                exps, key=lambda e: e.get("timestamp", ""), reverse=True
            )[0]
            experiment_id = latest_rec.get("experiment_id", experiment_id)
            eval_metrics = latest_rec.get("metrics", eval_metrics)

        with active_runs_lock:
            # Prevent overwriting terminal state
            if active_runs[run_id]["status"] not in ("completed", "failed", "cancelled"):
                active_runs[run_id].update({
                    "status": "completed",
                    "current_stage": None,
                    "completed_at": datetime.now().isoformat(),
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
                })

    except ExecutionCancelledError as e:
        print(f"Pipeline cooperative cancellation triggered: {e}", file=sys.stderr)
        with active_runs_lock:
            # Prevent overwriting terminal state
            if active_runs[run_id]["status"] not in ("completed", "failed", "cancelled"):
                active_runs[run_id].update({
                    "status": "cancelled",
                    "current_stage": None,
                    "error": str(e),
                    "completed_at": datetime.now().isoformat(),
                })
    except Exception as e:
        import traceback
        print(f"Pipeline background execution error: {e}", file=sys.stderr)
        traceback.print_exc()

        with active_runs_lock:
            # Prevent overwriting terminal state
            if active_runs[run_id]["status"] not in ("completed", "failed", "cancelled"):
                current_run_state = active_runs.get(run_id, {})
                failed_stage = current_run_state.get("current_stage")
                completed_stages = current_run_state.get("completed_stages", [])

                active_runs[run_id].update({
                    "status": "failed",
                    "current_stage": failed_stage,
                    "completed_stages": completed_stages,
                    "failed_stage": failed_stage,
                    "error": str(e),
                    "completed_at": datetime.now().isoformat(),
                })
    finally:
        # Clean up run-scoped listener and cancel request
        event_bus.unsubscribe("*", on_event)
        event_bus.clear_cancel_request(run_id)


@app.route("/api/project/run", methods=["POST"])
def run_pipeline():
    """Start background ML pipeline execution."""
    try:
        if request.content_length and request.content_length > 0 and not request.is_json:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Content-Type must be application/json"
                }
            }), 415

        try:
            data = request.get_json() or {}
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must contain valid JSON."
                }
            }), 400

        dataset_path = data.get("dataset_path")
        target_column = data.get("target_column")

        if not dataset_path:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset path is required"
                }
            }), 400

        project_root = get_active_project_path()
        if not (project_root / ".mlos").is_dir():
            return jsonify({
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": "No project initialized. Initialize a project first."
                }
            }), 400

        # Resolve path
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_root / dataset_path).resolve()

        # Workspace isolation check
        try:
            path_resolved.relative_to(project_root)
        except ValueError:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset outside workspace"
                }
            }), 400

        if not path_resolved.exists():
            return jsonify({
                "error": {
                    "code": "DATASET_NOT_FOUND",
                    "message": f"Dataset file does not exist at: {path_resolved}"
                }
            }), 404

        # Verify dataset format
        suffix = path_resolved.suffix.lower()
        if suffix not in [".csv", ".parquet"]:
            return jsonify({
                "error": {
                    "code": "DATASET_INVALID",
                    "message": "Unsupported file type. Only CSV and Parquet are supported."
                }
            }), 400

        try:
            if suffix == ".csv":
                df_temp = pd.read_csv(path_resolved, nrows=2)
            else:
                df_temp = pd.read_parquet(path_resolved)

            if target_column and target_column not in df_temp.columns:
                return jsonify({
                    "error": {
                        "code": "TARGET_NOT_FOUND",
                        "message": f"Target column '{target_column}' not found in dataset."
                    }
                }), 400
        except Exception as read_err:
            return jsonify({
                "error": {
                    "code": "DATASET_INVALID",
                    "message": f"Failed to read dataset: {str(read_err)}"
                }
            }), 400

        # Check if a run is already active
        with active_runs_lock:
            active_running = [
                rid for rid, info in active_runs.items() 
                if info.get("status") in ("queued", "running", "cancel_requested")
            ]
            if active_running:
                return jsonify({
                    "error": {
                        "code": "RUN_ALREADY_ACTIVE",
                        "message": f"A pipeline run is already active (Run ID: {active_running[0]})."
                    }
                }), 400

            run_id = str(uuid.uuid4())

            active_runs[run_id] = {
                "run_id": run_id,
                "status": "queued",
                "current_stage": None,
                "completed_stages": [],
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "error": None,
            }

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
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to start pipeline: {str(e)}"
            }
        }), 500


@app.route("/api/project/run/status/<run_id>", methods=["GET"])
def get_run_status(run_id):
    """Poll the status of an active pipeline execution."""
    with active_runs_lock:
        if run_id not in active_runs:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Run ID not found"
                }
            }), 404
        return jsonify(active_runs[run_id])


@app.route("/api/project/run/cancel/<run_id>", methods=["POST"])
def cancel_run(run_id):
    """Request cooperative cancellation of a pipeline run."""
    with active_runs_lock:
        if run_id not in active_runs:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Run ID not found"
                }
            }), 404

        run_info = active_runs[run_id]
        status = run_info.get("status")

        if status in ("completed", "failed", "cancelled"):
            return jsonify({
                "error": {
                    "code": "INVALID_STATE",
                    "message": f"Cannot cancel run in {status} state."
                }
            }), 400

        from mlos.communication.event_bus import GlobalEventBus
        GlobalEventBus().request_cancel(run_id)
        run_info["status"] = "cancel_requested"

        return jsonify({
            "run_id": run_id,
            "status": "cancel_requested",
            "message": "Cancellation request submitted."
        })


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
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to list experiments: {str(e)}"
            }
        }), 500


@app.route("/api/experiments/<experiment_id>", methods=["GET"])
def get_experiment_details(experiment_id):
    """Retrieve details for a specific experiment run."""
    try:
        project_root = get_active_project_path()
        tracker = ExperimentTracker(project_root)
        exp = tracker.get_experiment(experiment_id)

        if not exp:
            return jsonify({
                "error": {
                    "code": "EXPERIMENT_NOT_FOUND",
                    "message": f"Experiment '{experiment_id}' not found"
                }
            }), 404

        return jsonify(exp)
    except Exception as e:
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to fetch experiment details: {str(e)}"
            }
        }), 500


@app.route("/api/experiments/compare", methods=["POST"])
def compare_experiments():
    """Compare two experiments side-by-side using the ExperimentComparator."""
    try:
        if request.content_length and request.content_length > 0 and not request.is_json:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Content-Type must be application/json"
                }
            }), 415

        try:
            data = request.get_json() or {}
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must contain valid JSON."
                }
            }), 400

        exp1_id = data.get("exp1")
        exp2_id = data.get("exp2")

        if not exp1_id or not exp2_id:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Both exp1 and exp2 IDs are required for comparison"
                }
            }), 400

        project_root = get_active_project_path()
        tracker = ExperimentTracker(project_root)

        if not tracker.get_experiment(exp1_id):
            return jsonify({
                "error": {
                    "code": "EXPERIMENT_NOT_FOUND",
                    "message": f"Experiment '{exp1_id}' not found"
                }
            }), 404

        if not tracker.get_experiment(exp2_id):
            return jsonify({
                "error": {
                    "code": "EXPERIMENT_NOT_FOUND",
                    "message": f"Experiment '{exp2_id}' not found"
                }
            }), 404

        comparator = ExperimentComparator(tracker)
        diff = comparator.compare_experiments(exp1_id, exp2_id)

        return jsonify(diff)
    except ValueError as ve:
        return jsonify({
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(ve)
            }
        }), 400
    except Exception as e:
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to compare experiments: {str(e)}"
            }
        }), 500


@app.route("/api/project/validate-dataset", methods=["POST"])
def validate_dataset():
    """Validate a dataset path inline."""
    try:
        if request.content_length and request.content_length > 0 and not request.is_json:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Content-Type must be application/json"
                }
            }), 415

        try:
            data = request.get_json() or {}
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must contain valid JSON."
                }
            }), 400

        dataset_path = data.get("dataset_path")
        target_column = data.get("target_column")
        if not dataset_path:
            return jsonify({
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset path is required"
                }
            }), 400

        project_root = get_active_project_path()
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_root / dataset_path).resolve()

        # Check workspace isolation traversal
        try:
            path_resolved.relative_to(project_root)
        except ValueError:
            return jsonify({
                "valid": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Dataset outside workspace."
                }
            }), 400

        if not path_resolved.exists():
            return jsonify({
                "valid": False,
                "error": {
                    "code": "DATASET_NOT_FOUND",
                    "message": "Dataset file was not found."
                }
            }), 404

        # Check unsupported file type
        suffix = path_resolved.suffix.lower()
        if suffix not in [".csv", ".parquet"]:
            return jsonify({
                "valid": False,
                "error": {
                    "code": "DATASET_INVALID",
                    "message": "Unsupported file type."
                }
            }), 400

        try:
            if suffix == ".csv":
                df_temp = pd.read_csv(path_resolved, nrows=2)
            else:
                df_temp = pd.read_parquet(path_resolved)

            if target_column and target_column not in df_temp.columns:
                return jsonify({
                    "valid": False,
                    "error": {
                        "code": "TARGET_NOT_FOUND",
                        "message": f"Target column '{target_column}' not found in dataset."
                    }
                }), 400
        except Exception as e:
            return jsonify({
                "valid": False,
                "error": {
                    "code": "DATASET_INVALID",
                    "message": f"Failed to read dataset: {str(e)}"
                }
            }), 400

        return jsonify({
            "valid": True,
            "path": str(dataset_path)
        })

    except Exception as e:
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to validate dataset: {str(e)}"
            }
        }), 500


@app.route("/api/project/files", methods=["GET"])
def list_workspace_files():
    """List CSV/Parquet files in active workspace safely, up to 3 levels deep."""
    try:
        project_root = get_active_project_path()
        files = []
        for root, dirs, filenames in os.walk(project_root):
            # Prune hidden dirs, pycache, egg-info, and virtualenvs
            dirs[:] = [
                d for d in dirs
                if not d.startswith('.')
                and d not in ['__pycache__', 'node_modules', 'venv', '.venv', 'build', 'dist', 'mlos.egg-info']
            ]

            rel_path = Path(root).relative_to(project_root)
            if len(rel_path.parts) > 3:
                continue

            for f in filenames:
                if f.endswith(('.csv', '.parquet')):
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(project_root)
                    files.append(str(rel_p).replace('\\', '/'))

        return jsonify({"files": files})
    except Exception as e:
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to list workspace files: {str(e)}"
            }
        }), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
