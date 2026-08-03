"""
Explainability domain models.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecisionEvidence:
    """
    Structured observations used to make a meta-reasoning decision.
    """

    statistics_used: tuple[str, ...] = field(default_factory=tuple)
    observations_used: tuple[str, ...] = field(default_factory=tuple)
    performance_metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionRule:
    """
    Sub-model representing a single policy evaluation rule.
    """

    rule_id: str
    condition_evaluated: str
    action_taken: str


@dataclass(frozen=True)
class DecisionTrace:
    """
    Explainability trace detailing optimized decisions.
    """

    triggered_rules: tuple[DecisionRule, ...] = field(default_factory=tuple)
    evidence: DecisionEvidence = field(default_factory=DecisionEvidence)
    optimization_objectives: dict[str, float] = field(default_factory=dict)
    confidence_score: float = 1.0
