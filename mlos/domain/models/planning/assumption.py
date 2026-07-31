"""
Assumption domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Assumption:
    """
    Explicitly states an assumption made during the planning cycle.
    """

    description: str

    validation_status: str
