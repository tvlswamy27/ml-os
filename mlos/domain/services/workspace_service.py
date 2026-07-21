"""
Workspace service.

Handles workspace-related operations.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import asdict
from pathlib import Path

from mlos.domain.models.workspace import Workspace
from mlos.storage.yaml_storage import YamlStorage


class WorkspaceService:
    """
    Service responsible for managing workspaces.
    """

    def __init__(self):
        self.storage = YamlStorage()

    def create_workspace(self, name: str, root_path: Path) -> Workspace:
        """
        Create a new workspace.
        """

        workspace = Workspace(
            name=name,
            root_path=root_path,
        )

        return workspace

    def save_workspace(self, workspace: Workspace) -> None:
        """
        Save workspace configuration.
        """
        workspace.root_path.mkdir(parents=True, exist_ok=True)
        data = workspace.to_dict()
        data["root_path"] = str(data["root_path"])
        
        self.storage.save(
            workspace.root_path / ".mlos" / "workspace.yaml",
            data,
        )