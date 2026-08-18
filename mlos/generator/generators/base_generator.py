"""
Base Generator.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext


class BaseGenerator(ABC):
    """
    Base class for all code generators.
    """

    @property
    @abstractmethod
    def supported_decision_type(self) -> str:
        """
        The decision type string matched by the registry (e.g. 'impute').
        """

    @abstractmethod
    def can_generate(
        self,
        decision: Decision,
    ) -> bool:
        """
        Returns True if this generator can generate code
        for the supplied decision.
        """

    @abstractmethod
    def generate(
        self,
        decision: Decision,
        context: GenerationContext | None = None,
    ) -> GeneratedCode:
        """
        Generate executable code.
        """
