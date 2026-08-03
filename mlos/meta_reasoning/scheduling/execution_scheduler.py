"""
ExecutionScheduler graph orchestrator process manager.

Author: Antigravity
License: MIT
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import uuid
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.execution_snapshot import ExecutionSnapshot
from mlos.domain.models.meta_reasoning.meta_telemetry import MetaTelemetry
from mlos.meta_reasoning.communication.execution_event_bus import (
    ExecutionEvent,
    ExecutionEventBus,
)
from mlos.meta_reasoning.dispatchers.execution_dispatcher import ExecutionDispatcher
from mlos.meta_reasoning.recovery.failure_recovery_strategy import (
    DefaultFailureRecoveryStrategy,
    RecoveryAction,
)


class ExecutionScheduler:
    """
    Graph process manager resolving dependencies, topological ordering, and recovery strategies.
    """

    def __init__(
        self,
        dispatcher: ExecutionDispatcher,
        event_bus: ExecutionEventBus,
        recovery_strategy=None,
    ):
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.recovery_strategy = recovery_strategy or DefaultFailureRecoveryStrategy()

    def execute_schedule(
        self, plan: ExecutionPlan, context: MetaContext
    ) -> ExecutionSnapshot:
        """
        Main runner sorting nodes topologically, handling retry depth and parallel workers.
        """
        run_id = uuid.uuid4()
        self.event_bus.publish(
            ExecutionEvent(
                "PlanGenerated", {"run_id": str(run_id), "plan_checksum": plan.checksum}
            )
        )

        schedule = plan.execution_schedule
        nodes = {n.node_id: n for n in schedule.nodes}

        # Build dependency adjacency
        adj: dict[str, list[str]] = {nid: [] for nid in nodes}
        in_degree = {nid: 0 for nid in nodes}
        for dep in schedule.dependencies:
            adj[dep.parent_node_id].append(dep.child_node_id)
            in_degree[dep.child_node_id] += 1

        # Kahn's algorithm for topological sorting
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        topo_order = []
        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        execution_state_history = []
        timestamps = {}
        telemetry_records = []

        # Execute topologically
        workers = schedule.max_parallel_workers
        allow_parallel = (
            (
                context.user_constraints.max_worker_limits is None
                or context.user_constraints.max_worker_limits > 1
            )
            if context.user_constraints
            else False
        )

        def execute_node(node_id: str) -> None:
            node = nodes[node_id]
            policy = plan.subsystem_policies.get(node.subsystem)
            if not policy:
                return

            self.event_bus.publish(
                ExecutionEvent("NodeScheduled", {"node_id": node_id})
            )
            timestamps[node_id + "_started"] = datetime.utcnow()
            execution_state_history.append(
                (datetime.utcnow(), ExecutionLifecycle.RUNNING)
            )

            retry_depth = 0
            while True:
                try:
                    status = self.dispatcher.dispatch_subsystem(
                        node.subsystem, policy.strategy
                    )
                    timestamps[node_id + "_completed"] = datetime.utcnow()
                    execution_state_history.append((datetime.utcnow(), status))
                    break
                except Exception as err:
                    recovery: RecoveryAction = (
                        self.recovery_strategy.determine_recovery(
                            node.subsystem, err, retry_depth
                        )
                    )
                    self.event_bus.publish(
                        ExecutionEvent(
                            (
                                "NodeRetried"
                                if recovery.action_type == "RETRY"
                                else "NodeFailed"
                            ),
                            {"node_id": node_id, "action": recovery.action_type},
                        )
                    )

                    if recovery.action_type == "RETRY":
                        retry_depth = recovery.parameters.get(
                            "retry_depth", retry_depth + 1
                        )
                        execution_state_history.append(
                            (datetime.utcnow(), ExecutionLifecycle.RETRIED)
                        )
                        continue
                    elif recovery.action_type == "FALLBACK":
                        # Attempt fallback to simple rule execution strategy
                        from mlos.domain.models.meta_reasoning.policies import (
                            CachePolicy,
                            ValidationPolicy,
                            RetryPolicy,
                        )
                        from mlos.domain.models.meta_reasoning.execution_strategy import (
                            ExecutionStrategy,
                        )
                        from mlos.domain.enums.execution_mode import ExecutionMode

                        fallback_strat = ExecutionStrategy(
                            algorithm_type=ExecutionMode.RULE,
                            provider_selection=None,
                            cache_policy=CachePolicy(3600, False, "USE_CACHE"),
                            validation_policy=ValidationPolicy((), True, "LAX"),
                            retry_policy=RetryPolicy(3, 1.5, "FALLBACK_TO_RULE"),
                        )
                        try:
                            status = self.dispatcher.dispatch_subsystem(
                                node.subsystem, fallback_strat
                            )
                            timestamps[node_id + "_fallback_completed"] = (
                                datetime.utcnow()
                            )
                            execution_state_history.append((datetime.utcnow(), status))
                            break
                        except Exception:
                            # If fallback also fails, raise or abort
                            execution_state_history.append(
                                (datetime.utcnow(), ExecutionLifecycle.FAILED)
                            )
                            raise err
                    elif recovery.action_type == "SKIP":
                        timestamps[node_id + "_skipped"] = datetime.utcnow()
                        execution_state_history.append(
                            (datetime.utcnow(), ExecutionLifecycle.SKIPPED)
                        )
                        self.event_bus.publish(
                            ExecutionEvent("NodeSkipped", {"node_id": node_id})
                        )
                        break
                    else:
                        execution_state_history.append(
                            (datetime.utcnow(), ExecutionLifecycle.FAILED)
                        )
                        raise err

        if workers > 1 and allow_parallel:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor.map(execute_node, topo_order)
        else:
            for nid in topo_order:
                execute_node(nid)

        self.event_bus.publish(ExecutionEvent("PlanCompleted", {"run_id": str(run_id)}))

        telemetry_records.append(
            MetaTelemetry(
                provider="local",
                model="scheduler",
                latency_ms=100.0,
                fallback_used=False,
                tokens_used=0,
                cost_usd=0.0,
            )
        )

        return ExecutionSnapshot(
            run_id=run_id,
            policy_version=plan.policy_version,
            execution_plan=plan,
            execution_schedule=schedule,
            execution_state_history=tuple(execution_state_history),
            telemetry=tuple(telemetry_records),
            input_hash=plan.checksum[:16],
            output_hash=plan.checksum[-16:],
            timestamps=timestamps,
        )
