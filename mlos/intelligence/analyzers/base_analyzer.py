"""
Base Analyzer.

Defines the contract for all intelligence analyzers.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile


class BaseAnalyzer(ABC):
    """
    Base class for all intelligence analyzers.
    """

    @abstractmethod
    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:
        """
        Analyze the project and enrich the ProjectProfile.
        """
