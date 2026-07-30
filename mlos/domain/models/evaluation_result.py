"""
Evaluation Result domain model.

Represents performance results and checks evaluated from a run.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from mlos.domain.models.base import BaseModel


@dataclass
class EvaluationResult(BaseModel):
    """
    Stores metrics and verification checks evaluated for a pipeline.
    """

    metrics: dict[str, float] = field(default_factory=dict)

    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """
        True if all checks passed. Returns True if there are no checks.
        """
        if not self.checks:
            return True
        return all(self.checks.values())
