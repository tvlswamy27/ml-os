"""
Task domain model.

Represents a single machine learning engineering task.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel


@dataclass
class Task(BaseModel):
    """
    Represents a unit of work inside an ML project.
    """

    id: str

    title: str

    description: str

    status: str = "Pending"

    depends_on: list[str] = field(default_factory=list)

    deliverable: str | None = None