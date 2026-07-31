from mlos.domain.models.learning.learning_context import LearningContext
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.learning.algorithms.learning_algorithm import LearningAlgorithm


class LearningEngine:
    """
    Stateless subsystem engine delegating context processing to an injected algorithm.
    """

    def __init__(self, learning_algorithm: LearningAlgorithm | None = None):
        if learning_algorithm is None:
            from mlos.learning.algorithms.rule_based_learning_algorithm import (
                RuleBasedLearningAlgorithm,
            )

            learning_algorithm = RuleBasedLearningAlgorithm()
        self.learning_algorithm = learning_algorithm

    def learn(self, context: LearningContext) -> LearningSession:
        """Runs the pipeline learning step on the decoupled context."""
        return self.learning_algorithm.learn(context)
