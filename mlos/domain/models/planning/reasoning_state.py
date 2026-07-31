"""
ReasoningState domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field
from collections.abc import Mapping


@dataclass(frozen=True)
class ReasoningState:
    """
    Represents the immutable structured state/facts analyzed from observations.
    """

    facts: Mapping[str, str] = field(default_factory=dict)
