from mlos.domain.models.knowledge.knowledge_context import KnowledgeContext
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.knowledge.algorithms.knowledge_algorithm import KnowledgeAlgorithm


class KnowledgeEngine:
    """
    Stateless subsystem engine delegating context processing to an injected algorithm.
    """

    def __init__(self, knowledge_algorithm: KnowledgeAlgorithm | None = None):
        if knowledge_algorithm is None:
            from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
                RuleBasedKnowledgeAlgorithm,
            )

            knowledge_algorithm = RuleBasedKnowledgeAlgorithm()
        self.knowledge_algorithm = knowledge_algorithm

    def manage(self, context: KnowledgeContext) -> KnowledgeSession:
        """Runs the pipeline knowledge decision step on the decoupled context."""
        return self.knowledge_algorithm.manage(context)
