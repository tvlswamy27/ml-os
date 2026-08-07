"""
MetaContext domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass
from datetime import datetime

from mlos.domain.models.dataset import Dataset
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.domain.models.knowledge_summary import KnowledgeSummary
from mlos.domain.models.meta_reasoning.historical_evidence import HistoricalEvidence
from mlos.domain.models.meta_reasoning.provider_capability import ProviderCapability
from mlos.domain.models.meta_reasoning.resource_allocation import ResourceAllocation


@dataclass(frozen=True)
class MetaContext:
    """
    Immutable inputs representing the meta-reasoner optimization context.
    """

    project_name: str
    project_goal: str
    dataset_summary: Dataset | None
    feature_session: FeatureSession | None
    knowledge_summary: KnowledgeSummary
    provider_registry: tuple[ProviderCapability, ...]
    user_constraints: ResourceAllocation
    feedback_evidence: HistoricalEvidence
    observed_at: datetime
