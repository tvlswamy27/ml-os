"""
Model Evaluator Contract.

Defines the interface for pluggable execution evaluators.

Author: Vikram Tanakala
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.models.evaluation_result import EvaluationResult as DomainEvaluationResult


class ModelEvaluator(ABC):
    """
    Abstract interface for evaluating pipeline execution run results.
    """

    @abstractmethod
    def can_evaluate(
        self,
        artifacts: EvaluationArtifacts,
        execution_result: ExecutionResult,
    ) -> bool:
        """
        Returns True if this evaluator is suited for the run artifacts or log details.
        """
        pass

    @abstractmethod
    def evaluate(
        self,
        artifacts: EvaluationArtifacts,
        execution_result: ExecutionResult,
    ) -> DomainEvaluationResult:
        """
        Perform metric evaluation and validation checks.
        """
        pass
