"""
Execution Service.

Coordinates translating ProjectMemory to ExecutionContext and orchestrating runs.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.execution_context import ExecutionContext
from mlos.domain.models.execution_session import ExecutionSession
from mlos.execution.execution_engine import ExecutionEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService


class ExecutionService:
    """
    Coordinates building execution contexts, executing code via ExecutionEngine, and persisting sessions.
    """

    def __init__(
        self,
        execution_engine: ExecutionEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.execution_engine = execution_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> ExecutionContext:
        """
        Translate ProjectMemory into an immutable ExecutionContext.
        """
        source = memory.pipeline_source
        if source is None:
            # Create a fallback empty source if None
            from mlos.domain.models.pipeline_source import PipelineSource

            source = PipelineSource(imports="", body="", code="")
        return ExecutionContext(project_memory=memory, pipeline_source=source)

    def run_execution(
        self, context: ExecutionContext | ProjectMemory
    ) -> ExecutionSession:
        """
        Accept ExecutionContext or ProjectMemory, delegate to ExecutionEngine, and return ExecutionSession.
        """
        if isinstance(context, ProjectMemory):
            # Legacy call where memory was passed to run_execution directly.
            # Route to self.execute() to perform context construction and persistence.
            return self.execute(context)
        from typing import cast

        res = self.execution_engine.execute(context)
        return cast(ExecutionSession, res)

    def execute(self, memory: ProjectMemory) -> ExecutionSession:
        """
        Orchestrate the complete execution flow.
        """
        context = self.build_context(memory)
        session = self.run_execution(context)
        self.project_memory_service.add_execution_session(memory, session)
        return session
