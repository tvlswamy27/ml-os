"""
Project Memory.

Stores everything ML-OS knows about a project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.project_profile import ProjectProfile
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.evaluation_result import EvaluationResult

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

    project_profile: ProjectProfile | None = None

    pipeline: Pipeline | None = None

    execution_result: ExecutionResult | None = None

    evaluation_result: EvaluationResult | None = None