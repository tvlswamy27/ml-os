"""
ExecutionMode Enum.

Author: Antigravity
License: MIT
"""

from enum import Enum


class ExecutionMode(Enum):
    """
    Available execution modes for cognitive subsystems.
    """

    RULE = "RULE"
    LLM = "LLM"
    HYBRID = "HYBRID"
