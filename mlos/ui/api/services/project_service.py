import os
from pathlib import Path
from sqlalchemy.orm import Session
from .. import models, schemas

class ProjectService:
    @staticmethod
    def validate_project_path(path_str: str) -> Path:
        """
        Validate and resolve project paths to prevent traversal escapes (../) and protect system paths.
        """
        if not path_str:
            raise ValueError("Project path cannot be empty.")
        
        # Enforce direct check for traversal sequence
        normalized = os.path.normpath(path_str)
        path_parts = normalized.split(os.sep)
        if ".." in path_parts or "." in path_parts:
            # Prevent directory traversal
            if any(part == ".." for part in path_parts):
                raise ValueError("Directory traversal sequence ('..') detected.")

        try:
            p = Path(path_str).resolve()
        except Exception as e:
            raise ValueError(f"Invalid path representation: {e}")
            
        # Allowed roots: User's home folder and repository working directory
        allowed_roots = [
            Path.home().resolve(),
            Path.cwd().resolve()
        ]
        
        is_inside_allowed = False
        for root in allowed_roots:
            try:
                # relative_to raises ValueError if p is not inside root
                p.relative_to(root)
                is_inside_allowed = True
                break
            except ValueError:
                pass
                
        if not is_inside_allowed:
            raise ValueError("Project path must reside within the home directory or workspace folder.")
            
        return p

    def __init__(self, db: Session):
        self.db = db

    def create_project(self, workspace_id: int, project_in: schemas.ProjectCreate) -> models.Project:
        validated_path = self.validate_project_path(project_in.project_path)
        
        # Ensure path directory exists
        validated_path.mkdir(parents=True, exist_ok=True)
        
        db_project = models.Project(
            workspace_id=workspace_id,
            project_name=project_in.project_name,
            project_path=str(validated_path)
        )
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def get_project_by_id(self, project_id: int) -> models.Project | None:
        return self.db.query(models.Project).filter(models.Project.id == project_id).first()

    def list_projects_for_workspace(self, workspace_id: int) -> list[models.Project]:
        return self.db.query(models.Project).filter(models.Project.workspace_id == workspace_id).all()
