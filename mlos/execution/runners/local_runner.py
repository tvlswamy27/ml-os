"""
Local Process Pipeline Runner.

Executes a pipeline entrypoint in a local python subprocess.

Author: Vikram Tanakala
License: MIT
"""

import subprocess
import sys
from datetime import datetime

from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline
from mlos.execution.contracts.pipeline_runner import PipelineRunner


class LocalProcessPipelineRunner(PipelineRunner):
    """
    Runs Python pipeline scripts locally using subprocesses.
    """

    def run(self, pipeline: Pipeline) -> ExecutionResult:
        start_time = datetime.now()

        try:
            # Launch Python interpreter targeting the pipeline script
            process = subprocess.run(
                [sys.executable, str(pipeline.entrypoint_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            status = "SUCCESS" if process.returncode == 0 else "FAILED"
            return ExecutionResult(
                status=status,
                start_time=start_time,
                end_time=datetime.now(),
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
            )
        except Exception as e:
            return ExecutionResult(
                status="FAILED",
                start_time=start_time,
                end_time=datetime.now(),
                stderr=str(e),
                exit_code=-1,
            )
