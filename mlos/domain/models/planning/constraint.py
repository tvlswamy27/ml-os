"""
Constraint domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constraint:
    """
    Defines architectural or resource limitations for the execution strategy.
    """

    name: str

    limit_type: str

    limit_value: str
