"""
FeatureLineage domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeatureLineage:
    """
    Lineage tracking for engineered/derived features.
    """

    parent_features: tuple[str, ...] = field(default_factory=tuple)
    transformation: str = (
        ""  # Description of transformation applied, e.g., 'log_transform', 'interaction'
    )
    generation_step: int = 0
