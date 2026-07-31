"""
Goal domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Goal:
    """
    Represents an optimization target for the ML-OS project.
    """

    name: str

    metric: str

    target_value: str
