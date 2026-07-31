"""
Base Generator.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode


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
        pass

    @abstractmethod
    def can_generate(
        self,
        decision: Decision,
    ) -> bool:
        """
        Returns True if this generator can generate code
        for the supplied decision.
        """
        pass

    @abstractmethod
    def generate(
        self,
        decision: Decision,
    ) -> GeneratedCode:
        """
        Generate executable code.
        """
        pass
