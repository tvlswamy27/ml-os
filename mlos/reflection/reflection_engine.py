"""
ReflectionEngine core orchestrator.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.reflection.reflection_context import ReflectionContext
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.reflection.algorithms.reflection_algorithm import ReflectionAlgorithm


class ReflectionEngine:
    """
    Orchestrator that delegates to an injected ReflectionAlgorithm.
    Keeps reasoning stateless and side-effect free.
    """

    def __init__(self, reflection_algorithm: ReflectionAlgorithm | None = None):
        """
        Initialize with injected dependency.
        """
        if reflection_algorithm is None:
            from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
                RuleBasedReflectionAlgorithm,
            )

            reflection_algorithm = RuleBasedReflectionAlgorithm()
        self.reflection_algorithm = reflection_algorithm

    def reflect(self, context: ReflectionContext) -> ReflectionSession:
        """
        Delegate reflection reasoning to the injected algorithm.
        """
        return self.reflection_algorithm.reflect(context)
