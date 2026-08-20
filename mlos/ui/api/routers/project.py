from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import threading
import uuid
import json
from pathlib import Path
import pandas as pd
from typing import List, Any, Dict

from ..database import get_db
from .auth import get_current_user
from .. import models, schemas
from ..services.project_service import ProjectService
from ..services.event_stream_service import EventStreamService

# Core ML-OS SDK/Engine modules
from mlos.cli.persistence import reconstruct_project_memory, update_project_config_from_memory, find_project_root
from mlos.sdk.project import MLProject
from mlos.engine.engine import MLOSEngine
from mlos.experiment.tracker import ExperimentTracker
from mlos.communication.event_bus import GlobalEventBus
from mlos.execution.exceptions import ExecutionCancelledError

router = APIRouter(prefix="/api", tags=["projects"])

# Memory store for active runs state trackers
active_runs: Dict[str, Dict[str, Any]] = {}
active_runs_lock = threading.Lock()


def verify_workspace_access(workspace_id: int, user_id: int, db: Session) -> models.Workspace:
    """Authorize user membership inside the workspace."""
    member = db.query(models.WorkspaceMember).filter(
        models.WorkspaceMember.workspace_id == workspace_id,
        models.WorkspaceMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "WORKSPACE_ACCESS_DENIED",
                "message": "You are not a member of this workspace."
            }
        )
    workspace = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WORKSPACE_NOT_FOUND",
                "message": "The specified workspace does not exist."
            }
        )
    return workspace


def verify_project_access(project_id: int, user_id: int, db: Session) -> models.Project:
    """Verify project association and workspace permissions."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": "The specified project does not exist."
            }
        )
    verify_workspace_access(project.workspace_id, user_id, db)
    return project


def background_run_pipeline(
    run_id: str, project_path: Path, dataset_path: str, target_column: str
):
    """Executes the pipeline run in a background thread and updates status maps via event hooks."""
    event_bus = GlobalEventBus()

    def on_event(event):
        if event.run_id != run_id and event.payload.get("run_id") != run_id:
            return

        with active_runs_lock:
            if run_id not in active_runs:
                return
            
            run_info = active_runs[run_id]
            # Protect against overwriting terminal states
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
        path_resolved = Path(dataset_path)
        if not path_resolved.is_absolute():
            path_resolved = (project_path / dataset_path).resolve()

        if not path_resolved.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {path_resolved}")

        # 1. Initialize MLProject canonically
        project = MLProject(
            dataset_path=str(path_resolved),
            target_column=target_column,
            project_path=str(project_path),
        )

        from mlos.experiment.ids import generate_experiment_id
        generated_exp_id = generate_experiment_id()

        # Check for cancel requests prior to starting
        if event_bus.is_cancel_requested(run_id):
            raise ExecutionCancelledError("Run cancelled before starting ExecutionRuntime.")

        # Trigger canonical run logic
        session = project.run(experiment_id=generated_exp_id, run_id=run_id)

        # Retrieve evaluation outputs
        eval_metrics = project.metrics()
        tracker = ExperimentTracker(str(project_path))
        exps = tracker.list_experiments()
        experiment_id = session.run.experiment_id
        if exps:
            latest_rec = sorted(
                exps, key=lambda e: e.get("timestamp", ""), reverse=True
            )[0]
            experiment_id = latest_rec.get("experiment_id", experiment_id)
            eval_metrics = latest_rec.get("metrics", eval_metrics)

        with active_runs_lock:
            if active_runs[run_id]["status"] not in ("completed", "failed", "cancelled"):
                active_runs[run_id].update({
                    "status": "completed",
                    "current_stage": None,
                    "completed_at": datetime.utcnow().isoformat(),
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
        with active_runs_lock:
            if active_runs[run_id]["status"] not in ("completed", "failed", "cancelled"):
                active_runs[run_id].update({
                    "status": "cancelled",
                    "current_stage": None,
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat(),
                })
    except Exception as e:
        with active_runs_lock:
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
                    "completed_at": datetime.utcnow().isoformat(),
                })
    finally:
        event_bus.unsubscribe("*", on_event)
        event_bus.clear_cancel_request(run_id)


# --- Workspace Routes ---

@router.get("/workspaces", response_model=List[schemas.WorkspaceResponse])
def list_workspaces(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(models.WorkspaceMember).filter(models.WorkspaceMember.user_id == current_user.id).all()
    workspace_ids = [m.workspace_id for m in memberships]
    return db.query(models.Workspace).filter(models.Workspace.id.in_(workspace_ids)).all()


@router.post("/workspaces", response_model=schemas.WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace_in: schemas.WorkspaceCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = models.Workspace(name=workspace_in.name, owner_id=current_user.id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    # Add as admin member
    member = models.WorkspaceMember(workspace_id=workspace.id, user_id=current_user.id, role="admin")
    db.add(member)
    db.commit()
    return workspace


# --- Project Routes ---

@router.get("/projects", response_model=List[schemas.ProjectResponse])
def list_projects(workspace_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_workspace_access(workspace_id, current_user.id, db)
    return db.query(models.Project).filter(models.Project.workspace_id == workspace_id).all()


@router.post("/projects", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(workspace_id: int, project_in: schemas.ProjectCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_workspace_access(workspace_id, current_user.id, db)
    project_service = ProjectService(db)
    
    # Secure project directory traversal check
    try:
        project_service.validate_project_path(project_in.project_path)
    except ValueError as path_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PROJECT_PATH",
                "message": str(path_err)
            }
        )
        
    return project_service.create_project(workspace_id, project_in)


@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return verify_project_access(project_id, current_user.id, db)


@router.get("/projects/{project_id}/details")
def get_project_details(project_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = verify_project_access(project_id, current_user.id, db)
    project_root = Path(project.project_path)
    
    memory = reconstruct_project_memory(project_root)
    if not memory:
        return {
            "id": project.id,
            "project_name": project.project_name,
            "project_path": project.project_path,
            "status": "no_project",
            "dataset": None,
            "profile": None,
            "metrics": {},
            "decisions": [],
            "recommendations": []
        }
        
    # Read last experiment / metrics from tracker
    tracker = ExperimentTracker(str(project_root))
    exps = tracker.list_experiments()
    latest_metrics = {}
    if exps:
        latest_rec = sorted(
            exps, key=lambda e: e.get("timestamp", ""), reverse=True
        )[0]
        latest_metrics = latest_rec.get("metrics", {})

    decisions_list = []
    for dec in memory.decisions:
        decisions_list.append({
            "title": dec.title,
            "strategy": dec.strategy,
            "confidence": dec.confidence,
            "reason": dec.reason,
        })
        
    recs_list = []
    for rec in memory.recommendations:
        recs_list.append({
            "priority": rec.priority.value if hasattr(rec.priority, 'value') else str(rec.priority),
            "title": rec.title,
            "description": rec.description,
        })

    return {
        "id": project.id,
        "project_name": project.project_name,
        "project_path": project.project_path,
        "status": "active",
        "dataset": {
            "path": memory.dataset.path if memory.dataset else None,
            "target": memory.dataset.target if memory.dataset else None,
            "problem_type": memory.dataset.problem_type if memory.dataset else None,
            "rows": memory.dataset.rows if memory.dataset else 0,
            "columns": memory.dataset.columns if memory.dataset else 0,
        } if memory.dataset else None,
        "profile": {
            "problem_type": memory.project_profile.problem_type if memory.project_profile else "Classification",
            "complexity": memory.project_profile.complexity if memory.project_profile else "low",
            "baseline_models": memory.project_profile.baseline_models if memory.project_profile else [],
            "risks": memory.project_profile.risks if memory.project_profile else [],
        } if memory.project_profile else None,
        "metrics": latest_metrics,
        "decisions": decisions_list,
        "recommendations": recs_list,
    }


@router.post("/projects/{project_id}/analyze")
def analyze_project_dataset(project_id: int, data: Dict[str, Any], current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = verify_project_access(project_id, current_user.id, db)
    
    dataset_path = data.get("dataset_path")
    target_column = data.get("target_column")
    
    if not dataset_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": "Dataset path is required."}
        )
        
    project_root = Path(project.project_path)
    
    # Secure path traversal check
    try:
        ProjectService.validate_project_path(str(project_root / dataset_path))
    except ValueError as path_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PATH_TRAVERSAL_REJECTED", "message": str(path_err)}
        )
        
    path_resolved = Path(dataset_path)
    if not path_resolved.is_absolute():
        path_resolved = (project_root / dataset_path).resolve()
        
    if not path_resolved.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset file does not exist at: {path_resolved}"}
        )
        
    suffix = path_resolved.suffix.lower()
    if suffix not in [".csv", ".parquet"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DATASET_INVALID", "message": "Unsupported file format. Only CSV and Parquet are supported."}
        )
        
    try:
        if suffix == ".csv":
            df_temp = pd.read_csv(path_resolved, nrows=2)
        else:
            df_temp = pd.read_parquet(path_resolved)
            
        if target_column and target_column not in df_temp.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "TARGET_NOT_FOUND", "message": f"Target column '{target_column}' not found."}
            )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DATASET_READ_FAILED", "message": f"Failed to read dataset: {str(e)}"}
        )
        
    memory = reconstruct_project_memory(project_root)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Failed to load project config memory."}
        )
        
    # Trigger MLOSEngine run_analysis
    engine = MLOSEngine()
    engine.project_memory = memory
    report = engine.run_analysis(str(path_resolved), target_column)
    update_project_config_from_memory(project_root, engine.project_memory)
    
    # Format and return decisions & recommendations
    decisions_list = []
    for dec in report.decisions:
        decisions_list.append({
            "title": dec.title,
            "strategy": dec.strategy,
            "confidence": dec.confidence,
            "reason": dec.reason,
        })
        
    recs_list = []
    for rec in report.recommendations:
        recs_list.append({
            "priority": rec.priority.value,
            "title": rec.title,
            "description": rec.description,
        })
        
    return {
        "dataset_summary": {
            "path": str(report.dataset.path),
            "rows": report.dataset.rows,
            "columns": report.dataset.columns,
        },
        "decisions": decisions_list,
        "recommendations": recs_list,
    }


@router.post("/projects/{project_id}/run")
def run_project_pipeline(project_id: int, data: Dict[str, Any], current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = verify_project_access(project_id, current_user.id, db)
    
    dataset_path = data.get("dataset_path")
    target_column = data.get("target_column")
    
    if not dataset_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": "Dataset path is required."}
        )
        
    project_root = Path(project.project_path)
    
    # Traversal security check
    try:
        ProjectService.validate_project_path(str(project_root / dataset_path))
    except ValueError as path_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PATH_TRAVERSAL_REJECTED", "message": str(path_err)}
        )
        
    path_resolved = Path(dataset_path)
    if not path_resolved.is_absolute():
        path_resolved = (project_root / dataset_path).resolve()
        
    if not path_resolved.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DATASET_NOT_FOUND", "message": f"Dataset file does not exist at: {path_resolved}"}
        )
        
    # Check if run is already active
    with active_runs_lock:
        active_running = [
            rid for rid, info in active_runs.items()
            if info.get("status") in ("queued", "running", "cancel_requested")
        ]
        if active_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "RUN_ALREADY_ACTIVE",
                    "message": f"A pipeline run is already active (Run ID: {active_running[0]})."
                }
            )
            
        run_id = str(uuid.uuid4())
        active_runs[run_id] = {
            "run_id": run_id,
            "status": "queued",
            "current_stage": None,
            "completed_stages": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
        }
        
    # Start thread worker
    thread = threading.Thread(
        target=background_run_pipeline,
        args=(run_id, project_root, str(path_resolved), target_column)
    )
    thread.start()
    
    return {"run_id": run_id, "message": "ML Pipeline started successfully."}


@router.get("/projects/{project_id}/run/status/{run_id}")
def get_project_run_status(project_id: int, run_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(project_id, current_user.id, db)
    
    with active_runs_lock:
        if run_id not in active_runs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RUN_NOT_FOUND", "message": "Run ID not found."}
            )
        return active_runs[run_id]


@router.post("/projects/{project_id}/run/cancel/{run_id}")
def cancel_project_run(project_id: int, run_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(project_id, current_user.id, db)
    
    with active_runs_lock:
        if run_id not in active_runs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RUN_NOT_FOUND", "message": "Run ID not found."}
            )
            
        run_info = active_runs[run_id]
        if run_info.get("status") in ("completed", "failed", "cancelled"):
            return {"message": "Run is already in a terminal state.", "status": run_info["status"]}
            
        run_info["status"] = "cancel_requested"
        
    GlobalEventBus().request_cancel(run_id)
    return {"message": "Cancellation request dispatched.", "run_id": run_id}


@router.get("/projects/{project_id}/run/events/{run_id}")
def get_project_run_events(project_id: int, run_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_project_access(project_id, current_user.id, db)
    
    # Stream events from the isolated EventStreamService
    return StreamingResponse(
        EventStreamService.subscribe(run_id),
        media_type="text/event-stream"
    )


@router.get("/projects/{project_id}/experiments", response_model=List[schemas.ExperimentRecordResponse])
def get_project_experiments(project_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = verify_project_access(project_id, current_user.id, db)
    
    # Secure project path validation check
    try:
        ProjectService.validate_project_path(project.project_path)
    except ValueError as path_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PROJECT_PATH",
                "message": str(path_err)
            }
        )
        
    project_root = Path(project.project_path)
    tracker = ExperimentTracker(str(project_root))
    
    experiments = tracker.list_experiments()
    
    # Clean up absolute filepaths to make them relative to project root
    sanitized_experiments = []
    for exp in experiments:
        sanitized_artifacts = {}
        if "artifacts" in exp:
            for k, val in exp["artifacts"].items():
                try:
                    p_val = Path(val)
                    if p_val.is_absolute() and p_val.is_relative_to(project_root):
                        sanitized_artifacts[k] = str(p_val.relative_to(project_root))
                    else:
                        sanitized_artifacts[k] = p_val.name
                except Exception:
                    sanitized_artifacts[k] = val
                    
        sanitized_exp = {**exp}
        sanitized_exp["artifacts"] = sanitized_artifacts
        
        # Ensure candidate_trials is present and formatted
        if "candidate_trials" not in sanitized_exp:
            sanitized_exp["candidate_trials"] = []
            
        sanitized_experiments.append(sanitized_exp)
        
    return sanitized_experiments

