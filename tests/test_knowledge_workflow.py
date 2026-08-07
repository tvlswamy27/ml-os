from datetime import datetime
from unittest.mock import MagicMock

import yaml  # type: ignore[import-untyped]

from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
from mlos.domain.models.project_memory import ProjectMemory
from mlos.engine.engine import MLOSEngine
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry


def test_workflow_engine_triggers_knowledge():
    """Verify WorkflowEngine runs knowledge management after learning."""
    engine = MagicMock(spec=MLOSEngine)
    engine.project_memory = ProjectMemory(project_name="wf-test", project_goal="test")
    engine.learning_service = MagicMock()
    engine.knowledge_service = MagicMock()
    engine.learn.return_value = MagicMock()
    engine.manage_knowledge.return_value = MagicMock()

    hooks = HookRegistry()
    wf = WorkflowEngine(
        engine,
        hooks,
        planning_service=MagicMock(),
        decision_service=MagicMock(),
        generation_service=MagicMock(),
        execution_service=MagicMock(),
        evaluation_service=MagicMock(),
        reflection_service=MagicMock(),
        learning_service=engine.learning_service,
        knowledge_service=engine.knowledge_service,
    )

    result = wf.run(dataset_path="dummy.csv")
    assert result.status == "SUCCESS"
    engine.learn.assert_called_once()
    engine.manage_knowledge.assert_called_once()


def test_yaml_safe_dump_of_knowledge():
    """Verify KnowledgeSession and entries serialize to YAML without RepresenterErrors."""
    version = KnowledgeVersion(
        version_number=1,
        parent_entry_id="parent-123",
        timestamp=datetime.now(),
        change_summary="Change",
        reason="Reason",
    )
    confidence = KnowledgeConfidence(
        score=0.9,
        uncertainty=0.1,
        support_count=2,
        usage_history_count=0,
        explanation="Explain",
    )
    entry = KnowledgeEntry(
        knowledge_id="entry-uuid",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="planning",
        target_component="componentX",
        parameters={"alpha": "1.0"},
        source_learning_sessions=("sess-abc",),
        evidence_summary="Summary",
        version=version,
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=confidence,
        status=KnowledgeStatus.ACTIVE,
    )
    session = KnowledgeSession(
        summary="YAML Serialization test", promoted_entries=[entry], conflicts=[]
    )

    data = session.to_dict()
    # Confirm Enums and nested models are converted to primitive values
    assert data["promoted_entries"][0]["status"] == "ACTIVE"
    assert data["promoted_entries"][0]["knowledge_type"] == "PARAMETER_PRIOR"
    assert isinstance(data["promoted_entries"][0]["version"]["timestamp"], str)

    # Attempt yaml safe dump
    dumped = yaml.safe_dump(data)
    assert "YAML Serialization test" in dumped
    assert "PARAMETER_PRIOR" in dumped
