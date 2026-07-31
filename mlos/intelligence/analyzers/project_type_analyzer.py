from mlos.intelligence.analyzers.base_analyzer import BaseAnalyzer
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.project_profile import ProjectProfile


class ProjectTypeAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        memory: ProjectMemory,
        profile: ProjectProfile,
    ) -> None:

        dataset = memory.dataset

        if dataset is None:
            return

        if dataset.target is None:
            return

        if self._is_binary_classification(
            dataset,
            profile,
        ):
            return

        if self._is_multiclass_classification(
            dataset,
            profile,
        ):
            return

        if self._is_regression(
            dataset,
            profile,
        ):
            return

        """if dataset is None:
            return

        if dataset.target is None:
            return

        target_column = dataset.target
        unique_count = dataset.unique_values.get(target_column)

        if unique_count is None:
            return

        if unique_count == 2:
            profile.problem_type = "Binary Classification"

        elif unique_count > 2:

            target_type = dataset.column_types.get(
                target_column
            )

            if target_type is None:
                return   

            if target_type == "categorical":
                profile.problem_type = "Multi-class Classification"

            else:
                profile.problem_type = "Regression"   """

    def _is_binary_classification(
        self,
        dataset,
        profile,
    ) -> bool:

        target_column = dataset.target
        unique_count = dataset.unique_values.get(target_column)

        if unique_count is None:
            return False

        if unique_count == 2:
            profile.problem_type = "Binary Classification"
            return True

        return False

    def _is_multiclass_classification(
        self,
        dataset,
        profile,
    ) -> bool:
        target_column = dataset.target
        unique_count = dataset.unique_values.get(target_column)

        if unique_count is None:
            return False

        if unique_count > 2:

            target_type = dataset.column_types.get(target_column)

            if target_type is None:
                return False

            if target_type == "categorical":
                profile.problem_type = "Multi-class Classification"
                return True

        return False

    def _is_regression(
        self,
        dataset,
        profile,
    ) -> bool:
        """
        Detect regression problems.
        """

        target_column = dataset.target

        unique_count = dataset.unique_values.get(target_column)

        if unique_count is None:
            return False

        if unique_count <= 2:
            return False

        target_type = dataset.column_types.get(target_column)

        if target_type is None:
            return False

        if target_type == "numerical":
            profile.problem_type = "Regression"
            return True

        return False
