"""
Integration tests for the FeatureService.

Author: Antigravity
License: MIT
"""

from unittest.mock import MagicMock

import pandas as pd

from mlos.domain.models.dataset import Dataset
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.feature_service import FeatureService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.feature_intelligence.feature_engine import FeatureEngine


def test_build_context_mapping():
    """
    Verify that build_context translates full ProjectMemory to FeatureContext.
    """
    engine = MagicMock(spec=FeatureEngine)
    memory_service = MagicMock(spec=ProjectMemoryService)
    service = FeatureService(engine, memory_service)

    memory = ProjectMemory(
        project_name="FeatureProj",
        project_goal="Ensure feature accuracy",
    )
    dataset = Dataset(
        path="dummy_path.csv",
        target="label",
    )
    memory.dataset = dataset

    context = service.build_context(memory)

    assert context.project_name == "FeatureProj"
    assert context.project_goal == "Ensure feature accuracy"
    assert context.dataset.path == "dummy_path.csv"
    assert context.dataset.target == "label"


def test_analyze_features_orchestration(tmp_path):
    """
    Verify analyze_features loads data, runs engine, and persists session to ProjectMemory.
    """
    # 1. Create a dummy CSV file to load
    csv_file = tmp_path / "dummy_data.csv"
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "label": [0, 1, 0],
        }
    )
    df.to_csv(csv_file, index=False)

    # 2. Setup mock components
    engine = FeatureEngine()
    memory_service = ProjectMemoryService()
    service = FeatureService(engine, memory_service)

    memory = ProjectMemory(
        project_name="TestProj",
        project_goal="Test orchestration",
    )
    dataset = Dataset(
        path=str(csv_file),
        target="label",
        numerical_columns=["col1"],
        categorical_columns=[],
    )
    memory.dataset = dataset

    session = service.analyze_features(memory)

    # 3. Assertions
    assert isinstance(session, FeatureSession)
    assert session.status == "SUCCESS"
    assert len(memory.feature_sessions) == 1
    assert memory.feature_session == session
    assert "col1" in session.reasoning_state.feature_profiles
    assert session.consensus_ranking == ("col1",)
