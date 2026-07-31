"""
Simple Evaluator.

Parses metrics from EvaluationArtifacts or falls back to stdout.

Author: Vikram Tanakala
License: MIT
"""

import re
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.models.evaluation_result import (
    EvaluationResult as DomainEvaluationResult,
)
from mlos.evaluation.contracts.model_evaluator import ModelEvaluator


class SimpleEvaluator(ModelEvaluator):
    """
    Evaluator that parses metrics and performs basic threshold checks.
    """

    def can_evaluate(
        self,
        artifacts: EvaluationArtifacts,
        execution_result: ExecutionResult,
    ) -> bool:
        # Suitability matches if we have either artifacts metrics or process stdout to parse.
        return bool(artifacts.metrics or execution_result.stdout)

    def evaluate(
        self,
        artifacts: EvaluationArtifacts,
        execution_result: ExecutionResult,
    ) -> DomainEvaluationResult:
        metrics = {}

        # Load from artifacts first
        if artifacts.metrics:
            metrics.update(artifacts.metrics)

        # Fallback to parsing stdout if metrics dict is empty
        if not metrics and execution_result.stdout:
            stdout_lines = execution_result.stdout.splitlines()
            for line in stdout_lines:
                # Look for format "metric_name: value"
                match = re.search(r"([a-zA-Z_]+)\s*:\s*([0-9\.]+)", line)
                if match:
                    name, val_str = match.groups()
                    try:
                        metrics[name.lower()] = float(val_str)
                    except ValueError:
                        pass

        # Perform basic gate checks
        checks = {}
        if "accuracy" in metrics:
            checks["accuracy_threshold_passed"] = metrics["accuracy"] >= 0.80
        if "loss" in metrics:
            checks["loss_threshold_passed"] = metrics["loss"] <= 0.50

        return DomainEvaluationResult(
            metrics=metrics,
            checks=checks,
        )
