"""
Project State.

Represents the complete state of an ML project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel


@dataclass
class ProjectState(BaseModel):
    """
    Represents everything ML-OS knows about a project.
    """

    project_name: str

    goal: str

    dataset_path: str | None = None

    problem_type: str | None = None

    current_stage: str = "Project Creation"

    next_action: str = "Load dataset"

    completed_tasks: list[str] = field(default_factory=list)

    pending_tasks: list[str] = field(default_factory=list)

    observations: list[str] = field(default_factory=list)

    decisions: list[str] = field(default_factory=list)