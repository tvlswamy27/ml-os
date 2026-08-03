"""
SubsystemName Enum.

Author: Antigravity
License: MIT
"""

from enum import Enum


class SubsystemName(Enum):
    """
    Subsystem names within the ML-OS cognitive lifecycle.
    """

    PLANNING = "planning"
    DECISION = "decision"
    GENERATION = "generation"
    ASSEMBLY = "assembly"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"
    LEARNING = "learning"
    KNOWLEDGE = "knowledge"
