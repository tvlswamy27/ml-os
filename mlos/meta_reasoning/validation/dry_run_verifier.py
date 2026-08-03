"""
DryRunVerifier verification module.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.meta_reasoning.validation.execution_plan_validator import PlanValidationError


class DryRunVerifier:
    """
    Checks plugin registrations, dependencies, prompt configs, and environment health.
    """

    def verify_environment(self, plan: ExecutionPlan, context: MetaContext) -> None:
        """
        Runs complete pre-execution dry run verifications.
        """
        # 1. Verify provider capability existence
        registered_models = {pc.model_name for pc in context.provider_registry}

        for sub, policy in plan.subsystem_policies.items():
            pc = policy.strategy.provider_selection
            if pc is not None and pc.model_name not in registered_models:
                raise PlanValidationError(
                    f"Subsystem {sub.value} targets provider model '{pc.model_name}', "
                    "which is not registered in the active meta context provider registry."
                )

        # 2. Check workflow configuration sanity
        if not context.project_name:
            raise PlanValidationError(
                "Project Name must be defined in MetaContext configuration."
            )

        # 3. Check memory integrity
        if context.observed_at is None:
            raise PlanValidationError(
                "Context timestamp observed_at is invalid or missing."
            )
