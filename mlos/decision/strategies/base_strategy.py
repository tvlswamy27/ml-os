"""
Base strategy.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.decision import Decision


class BaseStrategy(ABC):
    """
    Base class for all decision strategies.
    """

    @abstractmethod
    def decide(
        self,
        memory: ProjectMemory,
    ) -> list[Decision]:
        """
        Generate decisions.
        """
        pass


from abc import ABC, abstractmethod


class DecisionStrategy(ABC):

    @abstractmethod
    def decide(
        self,
        memory,
    ):
        pass
