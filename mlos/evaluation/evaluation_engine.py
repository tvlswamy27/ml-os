"""
Evaluation Engine.

Stateless evaluation engine.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.models.evaluation_result import EvaluationResult as DomainEvaluationResult
from mlos.evaluation.contracts.model_evaluator import ModelEvaluator


class EvaluationEngine:
    """
    Stateless evaluation engine consolidating metrics and checks from registered evaluators.
    """

    def __init__(self):
        self.evaluators: list[ModelEvaluator] = []

    def register_evaluator(self, evaluator: ModelEvaluator) -> None:
        """
        Register a new evaluator plugin.
        """
        self.evaluators.append(evaluator)

    def evaluate(
        self,
        artifacts: EvaluationArtifacts,
        execution_result: ExecutionResult,
    ) -> DomainEvaluationResult:
        """
        Loops through evaluators and returns a consolidated EvaluationResult.
        """
        consolidated_metrics = {}
        consolidated_checks = {}

        for evaluator in self.evaluators:
            if evaluator.can_evaluate(artifacts, execution_result):
                res = evaluator.evaluate(artifacts, execution_result)
                consolidated_metrics.update(res.metrics)
                consolidated_checks.update(res.checks)

        return DomainEvaluationResult(
            metrics=consolidated_metrics,
            checks=consolidated_checks,
        )
