"""
Project Memory Service.
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.evaluation_result import EvaluationResult


class ProjectMemoryService:
    """
    Manages project memory.
    """

    def create(
        self,
        project_name: str,
        project_goal: str,
    ) -> ProjectMemory:

        return ProjectMemory(
            project_name=project_name,
            project_goal=project_goal,
        )
    
    def update_dataset(
        self,
        memory: ProjectMemory,
        dataset,
    ) -> ProjectMemory:
      """
      Attach dataset information to project memory.
      """

      memory.dataset = dataset

      return memory

    def update_execution_result(
        self,
        memory: ProjectMemory,
        execution_result: ExecutionResult,
    ) -> ProjectMemory:
        """
        Attach execution result to project memory.
        """
        memory.execution_result = execution_result
        return memory

    def update_pipeline(
        self,
        memory: ProjectMemory,
        pipeline: Pipeline,
    ) -> ProjectMemory:
        """
        Attach pipeline reference to project memory.
        """
        memory.pipeline = pipeline
        return memory

    def update_evaluation_result(
        self,
        memory: ProjectMemory,
        evaluation_result: EvaluationResult,
    ) -> ProjectMemory:
        """
        Attach evaluation result to project memory.
        """
        memory.evaluation_result = evaluation_result
        return memory