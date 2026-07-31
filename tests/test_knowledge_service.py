from uuid import uuid4
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.domain.models.learning.learning_evidence import LearningEvidence
from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.domain.services.knowledge_service import KnowledgeService
from mlos.knowledge.knowledge_engine import KnowledgeEngine


def test_knowledge_service_context_and_superseded_deprecation():
    """Verify context mapping and deprecation flow in KnowledgeService."""
    pm_service = ProjectMemoryService()
    engine = KnowledgeEngine()
    service = KnowledgeService(engine, pm_service)

    memory = ProjectMemory(
        project_name="Test-Service",
        project_goal="Ensure deprecations",
    )

    # 1. Setup mock learning session
    evidence = LearningEvidence(
        reflection_session_ids=(),
        evaluation_session_ids=(),
        execution_session_ids=(),
        metrics_used=(),
        confidence_values=(),
        frequency_counts={},
        trend_information={},
        supporting_observations=("Improved accuracy observed",),
    )
    upd = LearningUpdate(
        update_id="upd-123",
        update_type=LearningUpdateType.BOOST_HEURISTIC_WEIGHT,
        target_subsystem="planning",
        target_component="selector",
        parameters={"priority": "high"},
        evidence=evidence,
    )
    l_conf = LearningConfidence(score=0.85, uncertainty=0.1, accepted=True)
    l_session = LearningSession(
        summary="Found 1 learning update", updates=[upd], confidence=l_conf
    )
    object.__setattr__(l_session, "id", uuid4())
    memory.learning_sessions.append(l_session)

    # 2. Run service management
    k_session = service.manage(memory)
    assert len(memory.knowledge_sessions) == 1
    assert len(memory.knowledge_entries) == 1

    entry1 = memory.knowledge_entries[0]
    assert entry1.status == KnowledgeStatus.ACTIVE
    assert entry1.parameters == {"priority": "high"}

    # 3. Setup a second learning session modifying the same component
    upd2 = LearningUpdate(
        update_id="upd-456",
        update_type=LearningUpdateType.BOOST_HEURISTIC_WEIGHT,
        target_subsystem="planning",
        target_component="selector",
        parameters={"priority": "maximum"},
        evidence=evidence,
    )
    l_session2 = LearningSession(
        summary="Found 1 more update", updates=[upd2], confidence=l_conf
    )
    object.__setattr__(l_session2, "id", uuid4())
    memory.learning_sessions.append(l_session2)

    # Run second management cycle
    service.manage(memory)

    assert len(memory.knowledge_sessions) == 2
    # Append-only should retain both versions in entries
    assert len(memory.knowledge_entries) == 2

    # Check that the first entry became DEPRECATED, and second is ACTIVE
    assert entry1.status == KnowledgeStatus.DEPRECATED
    entry2 = memory.knowledge_entries[1]
    assert entry2.status == KnowledgeStatus.ACTIVE
    assert entry2.parameters == {"priority": "maximum"}
    assert entry2.version.parent_entry_id == entry1.knowledge_id
