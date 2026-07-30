"""
Workflow Result domain model.

Represents the execution outcome of an ML-OS workflow run.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from mlos.domain.models.base import BaseModel


@dataclass
class WorkflowResult(BaseModel):
    """
    Represents the status and metadata of a completed lifecycle run.
    """

    status: str

    start_time: datetime

    end_time: datetime | None = None

    errors: dict[str, str] = field(default_factory=dict)
