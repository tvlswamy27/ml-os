"""
ExecutionSimulator module.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.meta_context import MetaContext


class SimulationReport:
    """
    Simulation outcomes summary.
    """

    def __init__(
        self,
        estimated_runtime_ms: float,
        estimated_cost_usd: float,
        estimated_token_usage: int,
        resource_utilization: dict[str, float],
        success_probability: float,
    ):
        self.estimated_runtime_ms = estimated_runtime_ms
        self.estimated_cost_usd = estimated_cost_usd
        self.estimated_token_usage = estimated_token_usage
        self.resource_utilization = resource_utilization
        self.success_probability = success_probability


class ExecutionSimulator:
    """
    Simulates execution costs, memory, latency, and failure bounds.
    """

    def simulate(self, plan: ExecutionPlan, context: MetaContext) -> SimulationReport:
        """
        Calculates and aggregates estimated plan execution characteristics.
        """
        total_latency = 0.0
        total_cost = 0.0
        total_tokens = 0
        total_cpu = 0.0
        max_mem = 0

        for policy in plan.subsystem_policies.values():
            res = policy.resources
            if res:
                if res.cost_budget_usd is not None:
                    total_cost += res.cost_budget_usd
                if res.token_budget is not None:
                    total_tokens += res.token_budget
                if res.cpu_cores_limit is not None:
                    total_cpu = max(total_cpu, res.cpu_cores_limit)
                if res.memory_limit_mb is not None:
                    max_mem = max(max_mem, res.memory_limit_mb)

        # Basic mock simulation latency profile
        total_latency = len(plan.subsystem_policies) * 3000.0

        return SimulationReport(
            estimated_runtime_ms=total_latency,
            estimated_cost_usd=total_cost,
            estimated_token_usage=total_tokens,
            resource_utilization={
                "cpu_cores_peak": total_cpu,
                "memory_mb_peak": float(max_mem),
            },
            success_probability=0.95,
        )
