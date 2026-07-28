"""
Project Memory.

Stores everything ML-OS knows about a project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel
from mlos.domain.models.dataset import Dataset


@dataclass
class ProjectMemory(BaseModel):
    """
    Stores project knowledge.
    """

    project_name: str

    project_goal: str

    dataset: Dataset | None = None

    current_stage: str = "Project Initialization"

    completed_tasks: list[str] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)