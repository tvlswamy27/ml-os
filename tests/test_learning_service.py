from uuid import uuid4
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.domain.services.learning_service import LearningService
from mlos.learning.learning_engine import LearningEngine


def test_learning_service_build_context_mapping_and_slicing():
    """Verify that build_context translates reflection sessions into summaries and enforces limits."""
    engine = LearningEngine()
    memory_service = ProjectMemoryService()
    service = LearningService(engine, memory_service, window_size=2)

    memory = ProjectMemory(project_name="LearningSvcProj", project_goal="Test Slicing")

    # Add 4 reflection sessions
    for i in range(4):
        # Create reflection feedback items
        fb = ReflectionFeedback(
            feedback_id=f"fb-{i}",
            target_subsystem="decision",
            target_component="Encoder",
            action_type="ADJUST_PARAM_PRIOR",
            parameters={"prior": f"value-{i}"},
            priority="HIGH",
            reason=f"Reason-{i}",
            expected_outcome="outcome",
        )
        conf = ReflectionConfidence(
            score=0.8,
            uncertainty=0.1,
            evidence=(),
            explanation="explanation",
            accepted=True,
        )
        session = ReflectionSession(
            summary=f"Reflection summary {i}",
            insights=[],
            feedback=[fb],
            confidence=conf,
        )
        # Avoid frozen reassign using setattr if necessary
        object.__setattr__(session, "id", uuid4())
        memory.reflection_sessions.append(session)

    context = service.build_context(memory)
    assert context.project_name == "LearningSvcProj"
    assert context.latest_reflection is not None
    assert context.latest_reflection.summary == "Reflection summary 3"

    # Sliced history should have exactly 2 elements (window_size=2)
    assert len(context.historical_reflections) == 2
    assert context.historical_reflections[0].summary == "Reflection summary 1"
    assert context.historical_reflections[1].summary == "Reflection summary 2"

    # Confirm feedback mapping matches
    latest_fb = context.latest_reflection.feedback[0]
    assert latest_fb.feedback_id == "fb-3"
    assert latest_fb.target_subsystem == "decision"
    assert latest_fb.target_component == "Encoder"
    assert latest_fb.action_type == "ADJUST_PARAM_PRIOR"
    assert latest_fb.parameters == {"prior": "value-3"}


def test_learning_confidence_acceptance():
    """Verify that LearningService confidence is accepted with stable reflection trends."""
    engine = LearningEngine()
    memory_service = ProjectMemoryService()
    service = LearningService(engine, memory_service, window_size=5)

    memory = ProjectMemory(project_name="ConfProj", project_goal="Verify confidence")

    # We populate 3 stable reflection sessions
    for i in range(3):
        fb = ReflectionFeedback(
            feedback_id=f"fb-{i}",
            target_subsystem="decision",
            target_component="Scaler",
            action_type="BOOST_HEURISTIC_WEIGHT",
            parameters={},
            priority="HIGH",
            reason="Good performance observed",
            expected_outcome="outcome",
        )
        conf = ReflectionConfidence(
            score=0.85,
            uncertainty=0.15,
            evidence=(),
            explanation="explanation",
            accepted=True,
        )
        session = ReflectionSession(
            summary=f"Reflection {i}", insights=[], feedback=[fb], confidence=conf
        )
        object.__setattr__(session, "id", uuid4())
        memory.reflection_sessions.append(session)

    res_session = service.learn(memory)
    assert res_session.confidence.accepted
    assert res_session.confidence.score == 0.85
    assert res_session.confidence.uncertainty == 0.20
    assert len(res_session.updates) == 1
