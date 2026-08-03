"""
Feature Intelligence Service.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.feature_intelligence import FeatureContext, FeatureSession
from mlos.domain.models.knowledge_summary import build_knowledge_summary
from mlos.feature_intelligence.feature_engine import FeatureEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.io.data_loader import DataLoader


class FeatureService:
    """
    Orchestrates building feature context, loading raw data, running engine, and persisting session.
    """

    def __init__(
        self,
        feature_engine: FeatureEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.feature_engine = feature_engine
        self.project_memory_service = project_memory_service
        self.data_loader = DataLoader()

    def build_context(self, memory: ProjectMemory) -> FeatureContext:
        """
        Translate ProjectMemory into an immutable FeatureContext.
        """
        knowledge_summary = build_knowledge_summary(memory)
        return FeatureContext(
            project_name=memory.project_name,
            project_goal=memory.project_goal,
            dataset=memory.dataset,
            knowledge_summary=knowledge_summary,
        )

    def analyze_features(self, memory: ProjectMemory) -> FeatureSession:
        """
        Orchestrates the feature intelligence flow.
        """
        if memory.dataset is None or not memory.dataset.path:
            raise ValueError("Dataset path is not set in project memory.")

        # Load raw dataset into a DataFrame (transient data)
        dataframe = self.data_loader.load(memory.dataset.path)

        context = self.build_context(memory)
        session = self.feature_engine.analyze(context, dataframe)

        # Persist session in memory
        self.project_memory_service.add_feature_session(memory, session)
        return session
