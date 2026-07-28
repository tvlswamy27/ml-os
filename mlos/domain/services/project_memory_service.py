"""
Project Memory Service.
"""

from mlos.domain.models.project_memory import ProjectMemory


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