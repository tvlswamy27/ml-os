"""
Evaluation Service.

Orchestrates loading execution artifacts and executing the evaluation run.

Author: Vikram Tanakala
License: MIT
"""

import json
from pathlib import Path

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.evaluation.evaluation_engine import EvaluationEngine


class EvaluationService:
    """
    Coordinates metrics extraction and validation checks registration.
    """

    def __init__(
        self,
        evaluation_engine: EvaluationEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.evaluation_engine = evaluation_engine
        self.project_memory_service = project_memory_service

    def run_evaluation(self, memory: ProjectMemory) -> None:
        """
        Loads artifacts, evaluates performance, and updates ProjectMemory.
        """
        if not memory.execution_result:
            raise RuntimeError("No execution result exists in ProjectMemory to evaluate.")

        # Attempt to load structured metrics.json from artifacts folder
        project_dir = Path("playground") / memory.project_name
        metrics_file = project_dir / "artifacts" / "metrics.json"

        metrics_dict = {}
        if metrics_file.exists():
            try:
                metrics_dict = json.loads(metrics_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Construct strongly typed EvaluationArtifacts
        artifacts = EvaluationArtifacts(metrics=metrics_dict)

        # Run Stateless Evaluation
        result = self.evaluation_engine.evaluate(
            artifacts=artifacts,
            execution_result=memory.execution_result,
        )

        # Update ProjectMemory
        self.project_memory_service.update_evaluation_result(memory, result)
