"""
FeatureGraph domain model representing feature nodes and relationship edges.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from typing import Any

from mlos.domain.enums.feature_type import FeatureType


@dataclass(frozen=True)
class FeatureNode:
    """
    Represents a single feature column in the graph.
    """

    column_name: str
    feature_type: FeatureType


@dataclass(frozen=True)
class FeatureEdge:
    """
    Represents a directed or undirected relationship between features.
    """

    source: str
    target: str
    edge_type: str  # "dependency", "correlation", "redundancy", "lineage"
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FeatureGraph:
    """
    Immutable representation of feature relationship networks.
    """

    nodes: dict[str, FeatureNode] = field(default_factory=dict)
    edges: list[FeatureEdge] = field(default_factory=list)
