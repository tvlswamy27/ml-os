from datetime import datetime

from mlos.domain.models.knowledge.knowledge_context import (
    KnowledgeContext,
    KnowledgeSummary,
    LearningSummary,
    LearningUpdateSummary,
)
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
    RuleBasedKnowledgeAlgorithm,
)
from mlos.knowledge.knowledge_engine import KnowledgeEngine


def test_rule_based_algorithm_no_history():
    """Verify that rule-based algorithm operates correctly with empty history."""
    algo = RuleBasedKnowledgeAlgorithm()
    engine = KnowledgeEngine(algo)

    context = KnowledgeContext(
        project_name="Test-Proj",
        project_goal="Goal",
        latest_learning=None,
        historical_learnings=(),
        existing_knowledge=KnowledgeSummary(active_entries=()),
    )

    session = engine.manage(context)
    assert len(session.promoted_entries) == 0
    assert len(session.conflicts) == 0
    assert "promoted 0 new policies" in session.summary.lower()


def test_deterministic_conflict_resolution():
    """Verify that conflict resolution prioritizes higher confidence and resolves correctly."""
    algo = RuleBasedKnowledgeAlgorithm()
    engine = KnowledgeEngine(algo)

    # Propose two updates on same target component: componentA
    u1 = LearningUpdateSummary(
        update_id="upd-1",
        update_type="BOOST_HEURISTIC_WEIGHT",
        target_subsystem="planning",
        target_component="componentA",
        parameters={"weight": "0.8"},
        confidence_score=0.6,
        evidence_observations=("Weak positive trend",),
    )
    u2 = LearningUpdateSummary(
        update_id="upd-2",
        update_type="BOOST_HEURISTIC_WEIGHT",
        target_subsystem="planning",
        target_component="componentA",
        parameters={"weight": "0.95"},
        confidence_score=0.85,  # u2 has higher confidence
        evidence_observations=("Strong positive trend",),
    )

    latest_learn = LearningSummary(
        session_id="learn-sess-1", updates=(u1, u2), confidence_accepted=True
    )

    context = KnowledgeContext(
        project_name="Test-Proj",
        project_goal="Goal",
        latest_learning=latest_learn,
        historical_learnings=(),
        existing_knowledge=KnowledgeSummary(active_entries=()),
    )

    session = engine.manage(context)
    # Both u1 and u2 compete, u2 should win
    assert len(session.promoted_entries) == 1
    winner = session.promoted_entries[0]
    assert winner.parameters == {"weight": "0.95"}
    assert winner.confidence.score == 0.85

    # Verify conflict logging
    assert len(session.conflicts) >= 1
    reject_conflicts = [
        c
        for c in session.conflicts
        if c.parameter_name == "weight"
        and any("Rejected" in str(v) for v in c.competing_values)
    ]
    assert len(reject_conflicts) > 0


def test_versioning_and_parent_links():
    """Verify version numbers increment and parent_entry_id matches when superseding."""
    algo = RuleBasedKnowledgeAlgorithm()
    engine = KnowledgeEngine(algo)

    from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
    from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
    from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion

    # Existing active entry
    parent = KnowledgeEntry(
        knowledge_id="old-entry-uuid",
        knowledge_type=KnowledgeEntryType.HEURISTIC_WEIGHT,
        target_subsystem="planning",
        target_component="componentB",
        parameters={"weight": "0.5"},
        source_learning_sessions=("sess-old",),
        evidence_summary="Previous run",
        version=KnowledgeVersion(
            version_number=1,
            parent_entry_id=None,
            timestamp=datetime.now(),
            change_summary="",
            reason="",
        ),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(0.5, 0.5, 1, 0, ""),
        status=KnowledgeStatus.ACTIVE,
    )

    u = LearningUpdateSummary(
        update_id="new-upd",
        update_type="BOOST_HEURISTIC_WEIGHT",
        target_subsystem="planning",
        target_component="componentB",
        parameters={"weight": "0.75"},
        confidence_score=0.9,
        evidence_observations=("Better observations",),
    )

    latest_learn = LearningSummary(
        session_id="learn-sess-2", updates=(u,), confidence_accepted=True
    )

    context = KnowledgeContext(
        project_name="Test-Proj",
        project_goal="Goal",
        latest_learning=latest_learn,
        historical_learnings=(),
        existing_knowledge=KnowledgeSummary(active_entries=(parent,)),
    )

    session = engine.manage(context)
    assert len(session.promoted_entries) == 1
    promoted = session.promoted_entries[0]
    assert promoted.version.version_number == 2
    assert promoted.version.parent_entry_id == "old-entry-uuid"
