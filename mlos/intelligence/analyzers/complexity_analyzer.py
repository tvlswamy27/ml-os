from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile
from mlos.intelligence.analyzers.base_analyzer import BaseAnalyzer


class ComplexityAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:
        """
        Analyze the project and enrich the ProjectProfile with complexity assessment.
        """
        dataset = memory.dataset

        if dataset is None:
            return

        if self._is_easy(
            dataset,
        ):
            profile.complexity = "Easy"

            return

        if self._is_medium(
            dataset,
        ):
            profile.complexity = "Medium"

            return

    def _is_easy(
        self,
        dataset,
    ) -> bool:

        if dataset.columns < 10 and dataset.rows < 1000:
            return True
        return False

    def _is_medium(
        self,
        dataset,
    ) -> bool:
        """
        Determine whether the dataset has medium complexity.
        """
        if dataset.columns < 50 and dataset.rows < 100000:
            return True
        return False

    def _is_hard(
        self,
        dataset,
    ) -> bool:
        """
        Determine whether the dataset has high complexity.
        """
        return True
