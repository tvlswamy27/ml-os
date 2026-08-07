"""
ReasoningState domain model.

Author: Vikram Tanakala
License: MIT
"""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReasoningState:
    """
    Represents the immutable structured state/facts analyzed from observations.
    """

    facts: Mapping[str, str] = field(default_factory=dict)
