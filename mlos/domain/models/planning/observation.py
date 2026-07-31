"""
Observation domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Observation:
    """
    A specific recorded fact observed from the environment or run execution telemetry.
    """

    source_subsystem: str

    metric_key: str

    metric_value: str

    observed_at: datetime
