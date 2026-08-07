"""
ReflectionFeedback domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReflectionFeedback:
    """
    Structured, machine-readable feedback recommendations for automated learning loops.
    """

    feedback_id: str
    target_subsystem: str  # e.g., "planning", "decision", "generation"
    target_component: str  # e.g., "XGBoostGenerator", "RuleBasedPlanningAlgorithm"
    action_type: str  # e.g., "ADJUST_PARAM", "CHANGE_STRATEGY", "ENABLE_IMPUTATION"
    parameters: dict[
        str, str
    ]  # Machine-readable parameters for the action (e.g. {"learning_rate": "0.01"})
    priority: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    reason: str  # Human-readable justification backed by insights
    expected_outcome: str  # Human-readable predicted change
