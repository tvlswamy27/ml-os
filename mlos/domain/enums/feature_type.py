"""
FeatureType Enum.

Author: Antigravity
License: MIT
"""

from enum import Enum


class FeatureType(Enum):
    """
    Enum representing the physical/logical type of a feature column.
    """

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    IDENTIFIER = "identifier"
    GEOSPATIAL = "geospatial"
    UNKNOWN = "unknown"
