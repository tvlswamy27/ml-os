"""
Execution Engine.

Stateless execution engine for ML-OS.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.execution_result import ExecutionResult
from mlos.execution.contracts.pipeline_runner import PipelineRunner


class ExecutionEngine:
    """
    Stateless execution engine that delegates runs to PipelineRunners.
    """

    def __init__(self, runner: PipelineRunner):
        self.runner = runner

    def execute(self, pipeline: Pipeline) -> ExecutionResult:
        """
        Executes a pipeline and returns the run result.
        """
        return self.runner.run(pipeline)
