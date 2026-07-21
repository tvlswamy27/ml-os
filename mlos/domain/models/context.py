"""
Context domain model.

Represents the current execution context of a Machine Learning project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.enums.stage import Stage
from mlos.domain.models.base import BaseModel


@dataclass
class Context(BaseModel):
    """
    Represents the current runtime context of a project.
    """

    current_stage: Stage = Stage.PROBLEM_UNDERSTANDING

    progress: float = 0.0