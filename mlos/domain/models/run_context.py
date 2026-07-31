"""
RunContext domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RunContext:
    """
    Shared orchestration run context context representing a single execution cycle.
    """

    run_id: str

    iteration_id: int

    project_id: str

    mode: str

    provider: str

    model: str

    start_time: datetime

    end_time: datetime | None = None
