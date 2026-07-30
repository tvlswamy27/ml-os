"""
Execution Service.

Coordinates execution steps and memory updates.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.execution.execution_engine import ExecutionEngine


class ExecutionService:
    """
    Service responsible for coordinating pipeline execution and state updates.
    """

    def __init__(
        self,
        execution_engine: ExecutionEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.execution_engine = execution_engine
        self.project_memory_service = project_memory_service

    def run_execution(self, memory: ProjectMemory) -> None:
        """
        Runs the pipeline in ProjectMemory and updates it with the execution result.
        """
        if not memory.pipeline:
            raise RuntimeError("No pipeline defined in ProjectMemory to execute.")

        result = self.execution_engine.execute(memory.pipeline)
        self.project_memory_service.update_execution_result(memory, result)
