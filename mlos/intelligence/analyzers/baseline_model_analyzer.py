from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile
from mlos.intelligence.analyzers.base_analyzer import BaseAnalyzer


class BaselineModelAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:
        """
        Analyze the project and enrich the ProjectProfile with baseline model assessment.
        """
        if profile.problem_type == "Binary Classification":
            profile.baseline_models = self._binary_models()
            return

        if profile.problem_type == "Multiclass Classification":
            profile.baseline_models = self._multiclass_models()
            return

        if profile.problem_type == "Regression":
            profile.baseline_models = self._regression_models()
            return

        """profile.baseline_models.extend(
            [
                "Logistic Regression",
                "Random Forest",
            ]
        )"""

    def _binary_models(
        self,
    ) -> list[str]:
        """
        Return a list of baseline models suitable for binary classification problems.
        """
        return [
            "Logistic Regression",
            "Random Forest",
        ]

    def _multiclass_models(self) -> list[str]:
        """
        Return a list of baseline models suitable for multiclass classification problems.
        """
        return [
            "Logistic Regression",
            "Random Forest",
            "Gradient Boosting",
        ]

    def _regression_models(self) -> list[str]:
        """
        Return a list of baseline models suitable for regression problems.
        """
        return [
            "Linear Regression",
            "Ridge Regression",
            "Random Forest Regressor",
        ]
