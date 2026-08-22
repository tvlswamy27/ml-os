from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Any, Dict, List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkspaceCreate(BaseModel):
    name: str

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    project_name: str
    project_path: str

class ProjectResponse(BaseModel):
    id: int
    workspace_id: int
    project_name: str
    project_path: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectDetailsResponse(BaseModel):
    id: int
    workspace_id: int
    project_name: str
    project_path: str
    created_at: datetime
    # We can add details here later if needed
    status: str
    features: List[str]

    class Config:
        from_attributes = True

class SSEEventPayload(BaseModel):
    run_id: str
    event_type: str
    stage: str
    timestamp: str
    payload: Dict[str, Any]


class ExperimentTrialResponse(BaseModel):
    trial_id: str
    model_name: str
    estimator_class: str
    metric: str
    score: float
    cv_mean: float
    cv_std: float
    cv_scores: List[float]
    parameters: Dict[str, Any]
    rank: int
    status: str
    selected: bool
    duration_seconds: float
    error: Optional[str] = None


class ExperimentRecordResponse(BaseModel):
    experiment_id: str
    timestamp: str
    dataset_fingerprint: str
    problem_type: str
    pipeline_id: str
    selected_model: str
    candidate_models: List[str]
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]
    cv_scores: List[float]
    training_time_s: float
    prediction_time_s: float
    memory_usage_mb: float
    feature_importance: Dict[str, float]
    artifacts: Dict[str, str]
    environment: Dict[str, str]
    status: str
    candidate_trials: List[ExperimentTrialResponse] = []


class ArtifactResponse(BaseModel):
    name: str
    relative_path: str
    size_bytes: int
    modified_at: datetime
    artifact_type: str
    downloadable: bool
    mime_type: str

