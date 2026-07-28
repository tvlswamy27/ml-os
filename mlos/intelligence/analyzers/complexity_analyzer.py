import profile

from mlos.intelligence.analyzers.base_analyzer import BaseAnalyzer
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile

class ComplexityAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:
        """
        Analyze the project and enrich the ProjectProfile with complexity assessment.
        """
        pass

        profile.complexity = "Medium"
        

    
