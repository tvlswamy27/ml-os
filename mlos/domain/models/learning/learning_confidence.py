from dataclasses import dataclass, field


@dataclass(frozen=True)
class LearningConfidence:
    """
    Quantifies the safety and accuracy of generated pipeline updates.
    Determines if proposals are clean enough to be considered for propagation.
    """

    score: float
    uncertainty: float
    evidence: tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""
    accepted: bool = False
