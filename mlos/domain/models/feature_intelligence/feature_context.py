"""
FeatureContext domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.knowledge_summary import KnowledgeSummary


@dataclass(frozen=True)
class FeatureContext:
    """
    Immutable inputs to the Feature Intelligence subsystem.
    """

    project_name: str
    project_goal: str
    dataset: Dataset | None = None
    knowledge_summary: KnowledgeSummary = field(default_factory=KnowledgeSummary)
    observed_at: datetime = field(default_factory=datetime.now)
