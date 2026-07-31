from dataclasses import dataclass, field

from mlos.domain.models.dataset import Dataset
from mlos.domain.models.decision import Decision
from mlos.domain.models.recommendation import Recommendation


@dataclass
class AnalysisReport:
    """
    Result of a complete analysis pipeline.
    """

    dataset: Dataset

    decisions: list[Decision] = field(default_factory=list)

    recommendations: list[Recommendation] = field(default_factory=list)
