"""
Confidence domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.planning.evidence import Evidence
from mlos.domain.models.planning.assumption import Assumption


@dataclass(frozen=True)
class Confidence:
    """
    Multi-dimensional confidence estimation model.
    """

    confidence_level: str

    supporting_evidence: list[Evidence] = field(default_factory=list)

    uncertainty: str = ""

    assumptions: list[Assumption] = field(default_factory=list)

    explanation: str = ""
