"""
Pipeline Runner Contract.

Defines the interface for executing a generated Pipeline.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline


class PipelineRunner(ABC):
    """
    Interface for implementing execution backends.
    """

    @abstractmethod
    def run(self, pipeline: Pipeline, run_id: str | None = None) -> ExecutionResult:
        """
        Execute the pipeline and return the result.
        """
