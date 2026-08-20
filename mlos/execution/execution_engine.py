"""
Execution Engine.

Stateless execution engine for ML-OS.

Author: Vikram Tanakala
License: MIT
"""

import hashlib
from datetime import datetime
from pathlib import Path

from mlos.domain.models.execution_context import ExecutionContext
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.pipeline import Pipeline
from mlos.execution.contracts.pipeline_runner import PipelineRunner


class ExecutionEngine:
    """
    Stateless execution engine that delegates runs to PipelineRunners.
    """

    def __init__(self, runner: PipelineRunner):
        self.runner = runner

    def execute(
        self, context: ExecutionContext | Pipeline
    ) -> ExecutionSession | ExecutionResult:
        """
        Executes a pipeline and returns the run result.
        """
        from mlos.domain.models.pipeline import Pipeline

        if isinstance(context, Pipeline):
            return self.runner.run(context)

        run_id = None
        if hasattr(context, "project_memory") and context.project_memory:
            run_id = context.project_memory.run_id

        pipeline = context.project_memory.pipeline
        if not pipeline:
            raise RuntimeError("No pipeline is registered in memory to execute.")

        start_time = datetime.now()
        res = self.runner.run(pipeline, run_id=run_id)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        # Calculate pipeline hash
        pipeline_hash = None
        if context.pipeline_source and context.pipeline_source.code:
            pipeline_hash = hashlib.sha256(
                context.pipeline_source.code.encode("utf-8")
            ).hexdigest()

        # Artifact discovery
        artifacts = {}
        model_path = None
        metrics_path = None
        from mlos.cli.persistence import find_project_root

        if hasattr(context, "project_root") and context.project_root:
            project_dir = Path(context.project_root)
        elif hasattr(context, "project_memory") and context.project_memory and context.project_memory.pipeline and context.project_memory.pipeline.entrypoint_path:
            project_dir = Path(context.project_memory.pipeline.entrypoint_path).parent.parent
        else:
            project_dir = find_project_root() or Path.cwd()

        artifacts_dir = project_dir / "artifacts"

        if artifacts_dir.exists():
            for p in artifacts_dir.glob("*"):
                if p.is_file():
                    # Register all files found in the artifacts directory
                    p_abs = str(p.resolve())
                    artifacts[p.name] = p_abs
                    if "model" in p.name.lower():
                        model_path = p_abs
                    elif "metric" in p.name.lower():
                        metrics_path = p_abs

        return ExecutionSession(
            pipeline_source=context.pipeline_source,
            status=res.status,
            start_time=start_time,
            end_time=end_time,
            stdout=res.stdout,
            stderr=res.stderr,
            exit_code=res.exit_code,
            duration_seconds=duration,
            artifacts=artifacts,
            model_path=model_path,
            metrics_path=metrics_path,
            pipeline_hash=pipeline_hash,
        )
