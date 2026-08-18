"""
Decision model.

Represents a decision made by ML-OS.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Decision:
    """
    Represents a preprocessing or modeling decision.
    """

    title: str

    strategy: str

    confidence: str

    reason: str

    columns: list[str] = field(default_factory=list)

    parameters: dict[str, Any] = field(default_factory=dict)

