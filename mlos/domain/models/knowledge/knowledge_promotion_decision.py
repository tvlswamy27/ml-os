"""
KnowledgePromotionDecision, KnowledgePromotionType, and KnowledgeImpact domain models.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from enum import Enum


class KnowledgePromotionType(str, Enum):
    """
    Subsystem-validated transitions for incoming updates and existing entries.
    """

    PROMOTE_ACTIVE = "PROMOTE_ACTIVE"
    PROMOTE_EXPERIMENTAL = "PROMOTE_EXPERIMENTAL"
    DEPRECATE = "DEPRECATE"
    KEEP_EXISTING = "KEEP_EXISTING"
    REJECT = "REJECT"


@dataclass(frozen=True)
class KnowledgeImpact:
    """
    Quantitative expected delta estimates from applying the promotion decision.
    """

    expected_accuracy_delta: float = 0.0
    expected_latency_delta: float = 0.0
    expected_memory_delta: float = 0.0
    expected_stability_delta: float = 0.0
    expected_explainability_delta: float = 0.0


@dataclass(frozen=True)
class KnowledgePromotionDecision:
    """
    Structured transition mapping proposed by the Knowledge layer.
    """

    decision_type: KnowledgePromotionType
    target_entry_id: str | None
    target_component: str
    target_subsystem: str
    promotion_reason: str
    confidence: float
    evidence: tuple[str, ...]
    expected_impact: KnowledgeImpact
