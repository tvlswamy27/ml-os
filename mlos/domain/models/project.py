"""
Project domain model.

Represents a Machine Learning project in ML-OS.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from pathlib import Path

from mlos.domain.enums.project_mode import ProjectMode
from mlos.domain.enums.project_status import ProjectStatus
from mlos.domain.models.base import BaseModel


@dataclass
class Project(BaseModel):
    """
    Represents a Machine Learning project.
    """

    name: str

    goal: str

    mode: ProjectMode

    root_path: Path

    status: ProjectStatus = ProjectStatus.INITIALIZED