"""
Intelligence Engine.

Builds an intelligent understanding of a machine learning project.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile
from mlos.intelligence.analyzers.baseline_model_analyzer import (
    BaselineModelAnalyzer,
)
from mlos.intelligence.analyzers.complexity_analyzer import (
    ComplexityAnalyzer,
)
from mlos.intelligence.analyzers.project_type_analyzer import (
    ProjectTypeAnalyzer,
)
from mlos.intelligence.analyzers.risk_analyzer import (
    RiskAnalyzer,
)


class IntelligenceEngine:
    """
    Generates a ProjectProfile using multiple analyzers.
    """

    def __init__(self):

        self.analyzers = [
            ProjectTypeAnalyzer(),
            ComplexityAnalyzer(),
            RiskAnalyzer(),
            BaselineModelAnalyzer(),
        ]

    def analyze(
        self,
        memory: ProjectMemory,
    ) -> ProjectProfile:
        """
        Analyze the project.
        """

        profile = ProjectProfile()

        for analyzer in self.analyzers:
            print(type(analyzer).__name__)
            analyzer.analyze(
                memory,
                profile,
            )

        return profile
