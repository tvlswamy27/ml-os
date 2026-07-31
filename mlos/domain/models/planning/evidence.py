"""
Evidence domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    """
    Empirical metric or telemetry result used to validate or invalidate a hypothesis.
    """

    source_metric: str

    result_value: str

    supports_hypothesis: bool
