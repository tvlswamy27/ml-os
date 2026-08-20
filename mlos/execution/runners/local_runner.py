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

    def run(self, pipeline: Pipeline, run_id: str | None = None) -> ExecutionResult:
        import time
        from mlos.communication.event_bus import GlobalEventBus
        from mlos.execution.exceptions import ExecutionCancelledError

        event_bus = GlobalEventBus()
        start_time = datetime.now()
        cmd = [sys.executable, str(pipeline.entrypoint_path)]
        process = None

        try:
            # Launch Python interpreter targeting the pipeline script inside its project directory
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(pipeline.entrypoint_path.parent.parent)
            )

            # Polling loop to support responsive cancellation
            cancelled = False
            while True:
                # Check exit status
                ret = process.poll()
                if ret is not None:
                    break

                # Check for cancellation requested globally
                if run_id and event_bus.is_cancel_requested(run_id):
                    cancelled = True
                    break

                time.sleep(0.1)

            if cancelled:
                # Terminate the process
                process.terminate()
                # Grace period of 1 second
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    # Still alive, kill it
                    process.kill()
                    process.wait()

                stdout, stderr = process.communicate()
                raise ExecutionCancelledError(f"Subprocess execution cancelled. Stderr: {stderr}")

            # Non-cancelled exit: read stdout and stderr
            stdout, stderr = process.communicate()
            status = "SUCCESS" if process.returncode == 0 else "FAILED"
            return ExecutionResult(
                status=status,
                start_time=start_time,
                end_time=datetime.now(),
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
            )
        except Exception as e:
            if isinstance(e, ExecutionCancelledError):
                raise e
            stderr_msg = str(e)
            if process:
                try:
                    process.kill()
                    process.wait()
                    _, errs = process.communicate()
                    stderr_msg = f"{stderr_msg}\nSubprocess stderr: {errs}"
                except Exception:
                    pass
            return ExecutionResult(
                status="FAILED",
                start_time=start_time,
                end_time=datetime.now(),
                stderr=stderr_msg,
                exit_code=-1,
            )
