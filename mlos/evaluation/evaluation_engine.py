"""
Evaluation Engine.

Stateless evaluation engine.

Author: Vikram Tanakala
License: MIT
"""

import json
from pathlib import Path

from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.models.evaluation_context import EvaluationContext
from mlos.domain.models.evaluation_result import (
    EvaluationResult as DomainEvaluationResult,
)
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.execution_result import ExecutionResult
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
        context: EvaluationContext | EvaluationArtifacts,
        execution_result: ExecutionResult | None = None,
    ) -> EvaluationSession | DomainEvaluationResult:
        """
        Loops through evaluators and returns either EvaluationSession or DomainEvaluationResult.
        """
        if isinstance(context, EvaluationArtifacts):
            # Legacy backward compatibility path
            consolidated_metrics = {}
            consolidated_checks = {}
            for evaluator in self.evaluators:
                if execution_result is not None and evaluator.can_evaluate(
                    context, execution_result
                ):
                    res = evaluator.evaluate(context, execution_result)
                    consolidated_metrics.update(res.metrics)
                    consolidated_checks.update(res.checks)
            return DomainEvaluationResult(
                metrics=consolidated_metrics,
                checks=consolidated_checks,
            )

        # New EvaluationContext path
        latest_session = context.execution_session
        if (
            latest_session is None
            and getattr(context, "project_memory", None)
            and getattr(context.project_memory, "execution_result", None)
        ):
            res_exec = context.project_memory.execution_result
            from mlos.domain.models.execution_session import (
                ExecutionSession as ExecSess,
            )
            from datetime import datetime
            from mlos.domain.models.pipeline_source import PipelineSource

            ps = PipelineSource(imports="", body="", code="")
            st = getattr(res_exec, "start_time", datetime.now())
            et = getattr(res_exec, "end_time", None) or st
            latest_session = ExecSess(
                pipeline_source=ps,
                status=getattr(res_exec, "status", "SUCCESS"),
                start_time=st,
                end_time=et,
                stdout=getattr(res_exec, "stdout", ""),
                stderr=getattr(res_exec, "stderr", ""),
                exit_code=getattr(res_exec, "exit_code", 0),
                duration_seconds=0.0,
            )

        if latest_session is None:
            return EvaluationSession(status="NO_EXECUTION")

        # Attempt to load structured metrics.json from artifacts folder
        from mlos.cli.persistence import find_project_root

        project_dir = None
        if hasattr(context, "project_root") and context.project_root:
            project_dir = Path(context.project_root)
        elif getattr(context, "project_memory", None) and getattr(
            context.project_memory, "project_name", None
        ):
            pname = context.project_memory.project_name
            candidate = Path("playground") / pname
            if candidate.exists():
                project_dir = candidate

        if not project_dir:
            project_dir = find_project_root() or Path.cwd()

        metrics_file = project_dir / "artifacts" / "metrics.json"

        metrics_dict = {}
        if metrics_file.exists():
            try:
                metrics_dict = json.loads(metrics_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        artifacts = EvaluationArtifacts(metrics=metrics_dict)

        # Map current ExecutionSession to legacy ExecutionResult for running evaluators
        exec_result = ExecutionResult(
            status=latest_session.status,
            start_time=latest_session.start_time,
            end_time=latest_session.end_time,
            stdout=latest_session.stdout,
            stderr=latest_session.stderr,
            exit_code=latest_session.exit_code,
        )

        consolidated_metrics = {}
        consolidated_checks = {}

        for evaluator in self.evaluators:
            if evaluator.can_evaluate(artifacts, exec_result):
                res = evaluator.evaluate(artifacts, exec_result)
                consolidated_metrics.update(res.metrics)
                consolidated_checks.update(res.checks)

        # Problem type discovery
        problem_type = None
        if context.project_memory.project_profile:
            problem_type = context.project_memory.project_profile.problem_type
        elif context.project_memory.dataset:
            problem_type = context.project_memory.dataset.problem_type

        # Filter problem-specific metrics
        classification_keys = {
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "loss",
            "log_loss",
            "cross_entropy",
        }
        regression_keys = {"rmse", "mae", "mse", "r2", "loss"}
        clustering_keys = {"silhouette_score", "davies_bouldin_index"}

        filtered_metrics = {}
        for k, v in consolidated_metrics.items():
            k_lower = k.lower()
            if (
                problem_type == "classification"
                and k_lower in classification_keys
                or problem_type == "regression"
                and k_lower in regression_keys
                or problem_type == "clustering"
                and k_lower in clustering_keys
            ):
                filtered_metrics[k_lower] = float(v)
            elif problem_type not in ("classification", "regression", "clustering"):
                # Default fallback: keep all
                filtered_metrics[k_lower] = float(v)

        # Standard general execution metrics
        general_metrics = {
            "execution_duration": float(latest_session.duration_seconds),
            "pipeline_success": 1.0 if latest_session.status == "SUCCESS" else 0.0,
            "artifact_generation": float(len(latest_session.artifacts)),
            "model_existence": (
                1.0
                if (
                    latest_session.model_path
                    and Path(latest_session.model_path).exists()
                )
                else 0.0
            ),
            "metrics_existence": (
                1.0
                if (
                    latest_session.metrics_path
                    and Path(latest_session.metrics_path).exists()
                )
                else 0.0
            ),
        }

        final_metrics = {**general_metrics, **filtered_metrics}

        return EvaluationSession(
            metrics=final_metrics,
            checks=consolidated_checks,
            status=latest_session.status,
        )
