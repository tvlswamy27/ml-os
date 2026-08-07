"""
Execution Result domain model.

Represents the execution telemetry of a pipeline run.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime

from mlos.domain.models.base import BaseModel


@dataclass
class ExecutionResult(BaseModel):
    """
    Represents the output and status of a pipeline execution process.
    """

    status: str

    start_time: datetime

    end_time: datetime | None = None

    stdout: str = ""

    stderr: str = ""

    exit_code: int | None = None
