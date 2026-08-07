"""
Evaluation Artifacts domain model.

Encapsulates execution artifacts loaded for evaluation.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel


@dataclass
class EvaluationArtifacts(BaseModel):
    """
    Structured container for parsed execution metrics.
    """

    metrics: dict[str, float] = field(default_factory=dict)
