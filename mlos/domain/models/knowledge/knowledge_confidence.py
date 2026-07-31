from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeConfidence:
    """
    Quantifies the safety and validation strength of a promoted KnowledgeEntry.
    """

    score: float
    uncertainty: float
    support_count: int
    usage_history_count: int
    explanation: str
