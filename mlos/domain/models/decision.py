"""
Decision model.

Represents a decision made by ML-OS.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass


@dataclass
class Decision:
    """
    Represents a preprocessing or modeling decision.
    """

    title: str

    strategy: str

    confidence: str

    reason: str
