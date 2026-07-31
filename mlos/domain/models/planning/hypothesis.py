"""
Hypothesis domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.planning.evidence import Evidence


@dataclass(frozen=True)
class Hypothesis:
    """
    An analytical hypothesis regarding potential pipeline improvements or dataset issues.
    """

    description: str

    target_component: str

    validation_method: str

    evidences: list[Evidence] = field(default_factory=list)

    state: str = "UNVERIFIED"
