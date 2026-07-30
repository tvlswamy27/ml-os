"""
Pipeline Runner Contract.

Defines the interface for executing a generated Pipeline.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.execution_result import ExecutionResult


class PipelineRunner(ABC):
    """
    Interface for implementing execution backends.
    """

    @abstractmethod
    def run(self, pipeline: Pipeline) -> ExecutionResult:
        """
        Execute the pipeline and return the result.
        """
        pass
