"""
ExecutionPlanValidator validator module.

Author: Antigravity
License: MIT
"""

from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.execution_constraints import ExecutionConstraints
from mlos.domain.enums.execution_mode import ExecutionMode


class PlanValidationError(ValueError):
    """
    Raised when an ExecutionPlan contract fails structural or constraint validations.
    """

    pass


class ExecutionPlanValidator:
    """
    Validates structural topology, DAG properties, and resources constraints of ExecutionPlans.
    """

    def validate(self, plan: ExecutionPlan, constraints: ExecutionConstraints) -> None:
        """
        Runs validation sweeps on the provided plan. Raises PlanValidationError on issues.
        """
        nodes = {n.node_id: n for n in plan.execution_schedule.nodes}

        # 1. Duplicate subsystem nodes check
        subsystems_seen = set()
        for n in plan.execution_schedule.nodes:
            if n.subsystem in subsystems_seen:
                raise PlanValidationError(
                    f"Duplicate execution node found for subsystem: {n.subsystem.value}"
                )
            subsystems_seen.add(n.subsystem)

        # 2. Dependency validation (parents exist in nodes)
        adj: dict[str, list[str]] = {node_id: [] for node_id in nodes}
        in_degree = {node_id: 0 for node_id in nodes}

        for dep in plan.execution_schedule.dependencies:
            if dep.parent_node_id not in nodes:
                raise PlanValidationError(
                    f"Dependency parent node '{dep.parent_node_id}' is not defined in the schedule."
                )
            if dep.child_node_id not in nodes:
                raise PlanValidationError(
                    f"Dependency child node '{dep.child_node_id}' is not defined in the schedule."
                )
            adj[dep.parent_node_id].append(dep.child_node_id)
            in_degree[dep.child_node_id] += 1

        # 3. DAG cycle detection (Kahn's algorithm)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(nodes):
            raise PlanValidationError(
                "Execution schedule graph contains cycles (not a valid DAG)."
            )

        # 4. Check for invalid provider assignments & resource constraint violations
        total_estimated_cost = 0.0
        total_estimated_tokens = 0

        for sub, policy in plan.subsystem_policies.items():
            strat = policy.strategy
            res = policy.resources

            # Invalid provider selection check
            if strat.algorithm_type in (ExecutionMode.LLM, ExecutionMode.HYBRID):
                if strat.provider_selection is None:
                    raise PlanValidationError(
                        f"Subsystem {sub.value} is configured for {strat.algorithm_type.value} "
                        "execution but has no provider capability details assigned."
                    )

            if res:
                if res.cost_budget_usd is not None:
                    total_estimated_cost += res.cost_budget_usd
                if res.token_budget is not None:
                    total_estimated_tokens += res.token_budget

        # Constraint violations check
        if constraints:
            if total_estimated_cost > constraints.max_cost:
                raise PlanValidationError(
                    f"Total estimated cost ${total_estimated_cost:.4f} violates "
                    f"maximum allowed budget of ${constraints.max_cost:.4f}."
                )
            if total_estimated_tokens > constraints.max_tokens:
                raise PlanValidationError(
                    f"Total estimated tokens {total_estimated_tokens} violates "
                    f"maximum allowed tokens of {constraints.max_tokens}."
                )
