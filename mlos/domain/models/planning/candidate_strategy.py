"""
CandidateStrategy domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.planning.confidence import Confidence


@dataclass(frozen=True)
class CandidateStrategy:
    """
    A proposed candidate execution strategy.
    """

    strategy_name: str

    description: str

    steps: list[str] = field(default_factory=list)

    confidence: Confidence | None = None
