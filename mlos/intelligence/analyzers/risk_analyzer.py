import profile

from mlos.intelligence.analyzers.base_analyzer import BaseAnalyzer
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile
from mlos.domain.models.risk import Risk

class RiskAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:
        """
        Analyze the project and enrich the ProjectProfile with risk assessment.
        """

        dataset = memory.dataset

        if dataset is None:
            return

        if self._has_missing_values(
            dataset,
        ):
            profile.risks.append(
                Risk(
                    title="Missing Values",
                    severity="High",
                    description="The dataset contains missing values.",
                    recommendation="Consider imputing or removing missing values.",
                    affected_columns=[
                        column
                        for column, count in dataset.missing_values.items()
                        if count > 0
                    ],
                )
            )


        #profile.risks.append("Missing Values")

    def _has_missing_values(
        self,
        dataset,
    ) -> bool:
        for count in dataset.missing_values.values():

            if count > 0:
                return True

        return False
        