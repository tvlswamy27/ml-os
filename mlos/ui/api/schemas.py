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
