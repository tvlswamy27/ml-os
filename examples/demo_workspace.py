from pathlib import Path

from mlos.domain.services.workspace_service import WorkspaceService

service = WorkspaceService()

workspace = service.create_workspace(
    name="ML-OS Workspace",
    root_path=Path("demo_workspace"),
)

service.save_workspace(workspace)

print("Workspace created successfully!")