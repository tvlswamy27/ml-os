from dataclasses import dataclass

from mlos.domain.models.learning.learning_evidence import LearningEvidence
from mlos.domain.models.learning.learning_update_type import LearningUpdateType


@dataclass(frozen=True)
class LearningUpdate:
    """
    Structured, machine-readable pipeline tuning configuration.
    Proposed as an optimization for downstream engines.
    """

    update_id: str
    update_type: LearningUpdateType
    target_subsystem: str  # e.g., "decision", "generation"
    target_component: str  # e.g., "XGBoostGenerator"
    parameters: dict[str, str]  # Machine-readable tuning instructions
    evidence: LearningEvidence  # Traceability details
