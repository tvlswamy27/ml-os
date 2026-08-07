"""
FailureRecoveryStrategy abstraction and implementations.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.enums.subsystem_name import SubsystemName


class RecoveryAction:
    """
    Sub-model carrying the recovery decisions.
    """

    def __init__(self, action_type: str, parameters: dict):
        self.action_type = action_type  # "RETRY", "FALLBACK", "SKIP", "ABORT", "REPLAN"
        self.parameters = parameters


class FailureRecoveryStrategy(ABC):
    """
    Abstract interface for managing recovery actions on step dispatch errors.
    """

    @abstractmethod
    def determine_recovery(
        self, subsystem: SubsystemName, error: Exception, retry_depth: int
    ) -> RecoveryAction:
        """
        Calculates recovery actions on subsystem failure.
        """


class DefaultFailureRecoveryStrategy(FailureRecoveryStrategy):
    """
    Default recovery strategy with simple retry thresholds and fallback behaviors.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def determine_recovery(
        self, subsystem: SubsystemName, error: Exception, retry_depth: int
    ) -> RecoveryAction:
        if retry_depth < self.max_retries:
            return RecoveryAction("RETRY", {"retry_depth": retry_depth + 1})

        # Subsystems that can be skipped safely
        if subsystem in (
            SubsystemName.REFLECTION,
            SubsystemName.LEARNING,
            SubsystemName.KNOWLEDGE,
        ):
            return RecoveryAction("SKIP", {})

        # Falls back to RULE mode for planning or decision
        if subsystem in (SubsystemName.PLANNING, SubsystemName.DECISION):
            return RecoveryAction("FALLBACK", {"mode": "RULE"})

        return RecoveryAction("ABORT", {})
