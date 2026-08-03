"""
RecommendationAction Enum.

Author: Antigravity
License: MIT
"""

from enum import Enum


class RecommendationAction(Enum):
    """
    Enum representing selection actions for Feature Intelligence recommendations.
    """

    KEEP = "KEEP"
    REMOVE = "REMOVE"
    TRANSFORM = "TRANSFORM"
    ENGINEER = "ENGINEER"
    MERGE = "MERGE"
    IGNORE = "IGNORE"
    DEFER = "DEFER"
