"""
Workflow Engine.

Directly orchestrates the ML-OS subsystems lifecycle sequence.

Author: Vikram Tanakala
License: MIT
"""

from datetime import datetime
import traceback

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.workflow_result import WorkflowResult
from mlos.workflow.workflow_hooks import HookRegistry, WorkflowHook


class WorkflowEngine:
    """
    Stateless workflow runner that executes ML lifecycle subsystems sequentially.
    """

    def __init__(self, mlos_engine, hooks: HookRegistry):
        self.mlos_engine = mlos_engine
        self.hooks = hooks

    def run(self, dataset_path: str, target: str | None = None) -> WorkflowResult:
        """
        Executes the unidirectional pipeline, triggers hooks, and returns a WorkflowResult.
        """
        start_time = datetime.now()
        errors = {}

        try:
            # 1. Analysis Subsystem
            self.hooks.trigger(WorkflowHook.BEFORE_ANALYSIS, dataset_path)
            self.mlos_engine.analyze(dataset_path)
            self.hooks.trigger(WorkflowHook.AFTER_ANALYSIS, self.mlos_engine.project_memory)

            # 2. Decision Subsystem
            decisions = self.mlos_engine.decision_engine.decide(self.mlos_engine.project_memory)

            # 3. Generator Subsystem
            generated_codes = self.mlos_engine.generator_engine.generate(decisions)

            # 4. Assembly Subsystem
            self.mlos_engine.assemble(generated_codes)

            # 5. Execution Subsystem
            self.hooks.trigger(WorkflowHook.BEFORE_EXECUTION, self.mlos_engine.project_memory)
            self.mlos_engine.execute()
            self.hooks.trigger(WorkflowHook.AFTER_EXECUTION, self.mlos_engine.project_memory)

            # 6. Evaluation Subsystem
            self.mlos_engine.evaluate()

        except Exception as e:
            errors["lifecycle_run"] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return WorkflowResult(
                status="FAILED",
                start_time=start_time,
                end_time=datetime.now(),
                errors=errors,
            )

        return WorkflowResult(
            status="SUCCESS",
            start_time=start_time,
            end_time=datetime.now(),
        )
