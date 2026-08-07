from unittest.mock import MagicMock

from mlos.domain.models.learning.learning_confidence import LearningConfidence
from mlos.domain.models.learning.learning_evidence import LearningEvidence
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update import LearningUpdate
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.domain.models.project_memory import ProjectMemory
from mlos.engine.engine import MLOSEngine
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry


def test_workflow_engine_triggers_learning():
    """Verify that WorkflowEngine.run() invokes learn() at the end."""
    mlos_engine = MagicMock(spec=MLOSEngine)
    mlos_engine.project_memory = ProjectMemory(
        project_name="TriggerLearn", project_goal="TestGoal"
    )
    mlos_engine.learning_service = MagicMock()
    mlos_engine.learn.return_value = MagicMock(spec=LearningSession)

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine,
        hooks,
        planning_service=MagicMock(),
        decision_service=MagicMock(),
        generation_service=MagicMock(),
        execution_service=MagicMock(),
        evaluation_service=MagicMock(),
        reflection_service=MagicMock(),
        learning_service=mlos_engine.learning_service,
    )

    res = workflow.run("dummy_dataset.csv")
    assert res.status == "SUCCESS"
    mlos_engine.learn.assert_called_once()


def test_persistence_serialization_deserialization(tmp_path):
    """Verify that YAML serialization/deserialization of learning sessions is fully trace-compatible."""
    from mlos.cli.persistence import (
        reconstruct_project_memory,
        update_project_config_from_memory,
    )

    # Create temp project directory structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / ".mlos").mkdir()

    # Create project memory with learning session
    memory = ProjectMemory(
        project_name="SerializationProj", project_goal="Test yaml IO"
    )

    upd = LearningUpdate(
        update_id="upd-123",
        update_type=LearningUpdateType.DISABLE_GENERATOR,
        target_subsystem="generation",
        target_component="EncodingGenerator",
        parameters={"generator": "Encoder"},
        evidence=LearningEvidence(
            reflection_session_ids=("ref-1",),
            evaluation_session_ids=("eval-1",),
            execution_session_ids=("exec-1",),
            metrics_used=("accuracy",),
            confidence_values=(0.9,),
            frequency_counts={"FAIL": 1},
            trend_information={"accuracy": "degrading"},
            supporting_observations=("Regression detected",),
        ),
    )
    conf = LearningConfidence(score=0.8, uncertainty=0.1, accepted=True)
    session = LearningSession(summary="Test Summary", updates=[upd], confidence=conf)
    memory.learning_sessions.append(session)

    # Serialize to disk
    update_project_config_from_memory(project_dir, memory)

    # Reconstruct from disk
    loaded_memory = reconstruct_project_memory(project_dir)
    assert loaded_memory.project_name == "SerializationProj"
    assert len(loaded_memory.learning_sessions) == 1

    loaded_session = loaded_memory.learning_sessions[0]
    assert loaded_session.summary == "Test Summary"
    assert loaded_session.confidence.accepted
    assert len(loaded_session.updates) == 1

    loaded_upd = loaded_session.updates[0]
    assert loaded_upd.update_type == LearningUpdateType.DISABLE_GENERATOR
    assert loaded_upd.target_component == "EncodingGenerator"
    assert loaded_upd.evidence.reflection_session_ids == ("ref-1",)


def test_learning_does_not_mutate_running_config():
    """Verify that Running learning doesn't change active execution states, only appends proposal updates."""
    engine = MLOSEngine()
    engine.create_project(
        name="NoMutationProj", goal="Verify learning is analytical only"
    )

    # Confirm initial list is empty
    assert len(engine.project_memory.learning_sessions) == 0
    assert engine.project_memory.current_stage == "Project Initialization"

    # Execute learn
    session = engine.learn()

    # Memory structures should not be modified, only the new LearningSession appended
    assert len(engine.project_memory.learning_sessions) == 1
    assert engine.project_memory.current_stage == "Project Initialization"
    assert session.updates[0].update_type == LearningUpdateType.REGISTER_PATTERN
    assert not session.confidence.accepted
