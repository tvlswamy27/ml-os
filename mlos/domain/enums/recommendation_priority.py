"""
Recommendation Priority.

Defines the priority levels for recommendations.

Author: Vikram Tanakala
License: MIT
"""

from enum import Enum


class RecommendationPriority(Enum):
    """
    Recommendation priority levels.
    """

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
