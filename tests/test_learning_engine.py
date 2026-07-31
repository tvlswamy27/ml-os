from unittest.mock import MagicMock
from mlos.learning.learning_engine import LearningEngine
from mlos.learning.algorithms.rule_based_learning_algorithm import (
    RuleBasedLearningAlgorithm,
)
from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_update_type import LearningUpdateType


def test_learning_engine_delegates_to_algorithm():
    """Verify that LearningEngine delegates directly to the injected algorithm."""
    algo = MagicMock(spec=RuleBasedLearningAlgorithm)
    engine = LearningEngine(algo)
    context = MagicMock(spec=LearningContext)

    engine.learn(context)
    algo.learn.assert_called_once_with(context)


def test_rule_based_algorithm_empty_history():
    """Verify that learning with an empty history generates initialization proposals."""
    algo = RuleBasedLearningAlgorithm()
    context = LearningContext(
        project_name="EmptyProj",
        project_goal="Test Initialization",
        latest_reflection=None,
        historical_reflections=(),
        window_size=10,
    )

    session = algo.learn(context)
    assert isinstance(session, LearningSession)
    assert not session.confidence.accepted
    assert len(session.updates) == 1

    upd = session.updates[0]
    assert upd.update_type == LearningUpdateType.REGISTER_PATTERN
    assert upd.target_subsystem == "system"
    assert upd.target_component == "pipeline"
    assert upd.parameters == {"status": "initialized"}
    assert "initialized" in upd.evidence.supporting_observations[0].lower()
