"""
MetaPlanner orchestration engine, MetaAlgorithm, and RuleBasedMetaAlgorithm.

Author: Antigravity
License: MIT
"""

import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.execution_plan import ExecutionPlan
from mlos.domain.models.meta_reasoning.execution_schedule import (
    ExecutionSchedule,
    ScheduleDependency,
    ScheduleNode,
)
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.meta_reasoning_state import MetaReasoningState
from mlos.domain.models.meta_reasoning.meta_session import MetaSession
from mlos.domain.models.meta_reasoning.policy_diff import PolicyDiff
from mlos.domain.models.meta_reasoning.policy_version import PolicyVersion
from mlos.meta_reasoning.optimization.optimization_strategy import OptimizationStrategy


class MetaAlgorithm(ABC):
    """
    Abstract Template Method base for Meta-Reasoning planning algorithms.
    """

    def __init__(self, optimizer: OptimizationStrategy):
        self.optimizer = optimizer

    def generate_plan(
        self, context: MetaContext, state: MetaReasoningState
    ) -> ExecutionPlan:
        """
        Template method orchestrating the planning phases.
        """
        self._profile_demands(context, state)
        self._evaluate_providers(context, state)

        # Pluggable Optimization
        policies = self.optimizer.optimize(context, state)

        # Schedule Synthesis
        schedule = self._synthesize_schedule(context, state, policies)

        # Version Lineage
        version_id = uuid.uuid4()
        policy_version = PolicyVersion(
            policy_id=version_id,
            version=1,
            parent_policy_id=None,
            generated_by=self.__class__.__name__,
            generated_at=datetime.utcnow(),
            superseded_by=None,
            effective_from=datetime.utcnow(),
        )

        # Checksum calculation for immutability contract
        prop_summary = {
            "policy_version_id": str(version_id),
            "policies": {
                k.value: {
                    "mode": v.strategy.algorithm_type.value,
                    "provider": (
                        v.strategy.provider_selection.model_name
                        if v.strategy.provider_selection
                        else None
                    ),
                }
                for k, v in policies.items()
            },
            "schedule_nodes": [n.node_id for n in schedule.nodes],
        }
        checksum_payload = json.dumps(prop_summary, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(checksum_payload).hexdigest()

        return ExecutionPlan(
            policy_version=policy_version,
            subsystem_policies=policies,
            execution_schedule=schedule,
            optimization_result={"global_utility_estimate": 1.0},
            planner_name=self.__class__.__name__,
            planner_version="1.0.0",
            generated_at=datetime.utcnow(),
            checksum=checksum,
        )

    @abstractmethod
    def _profile_demands(self, context: MetaContext, state: MetaReasoningState) -> None:
        pass

    @abstractmethod
    def _evaluate_providers(
        self, context: MetaContext, state: MetaReasoningState
    ) -> None:
        pass

    @abstractmethod
    def _synthesize_schedule(
        self, context: MetaContext, state: MetaReasoningState, policies: dict
    ) -> ExecutionSchedule:
        pass


class RuleBasedMetaAlgorithm(MetaAlgorithm):
    """
    Rule-based baseline meta planner algorithm.
    """

    def _profile_demands(self, context: MetaContext, state: MetaReasoningState) -> None:
        state.facts["demand_density"] = "HIGH" if context.dataset_summary else "LOW"

    def _evaluate_providers(
        self, context: MetaContext, state: MetaReasoningState
    ) -> None:
        state.facts["available_providers_count"] = str(len(context.provider_registry))

    def _synthesize_schedule(
        self, context: MetaContext, state: MetaReasoningState, policies: dict
    ) -> ExecutionSchedule:
        # Standard sequential schedule topological mapping
        order = [
            SubsystemName.PLANNING,
            SubsystemName.DECISION,
            SubsystemName.GENERATION,
            SubsystemName.ASSEMBLY,
            SubsystemName.EXECUTION,
            SubsystemName.EVALUATION,
            SubsystemName.REFLECTION,
            SubsystemName.LEARNING,
            SubsystemName.KNOWLEDGE,
        ]

        nodes = []
        dependencies = []

        for i, sub in enumerate(order):
            node_id = f"node_{sub.value}"
            nodes.append(
                ScheduleNode(
                    node_id=node_id,
                    subsystem=sub,
                    execution_condition="ALWAYS",
                    is_deferred=False,
                )
            )
            if i > 0:
                parent_id = f"node_{order[i-1].value}"
                dependencies.append(
                    ScheduleDependency(
                        parent_node_id=parent_id,
                        child_node_id=node_id,
                        dependency_type="SEQUENTIAL",
                    )
                )

        return ExecutionSchedule(
            nodes=tuple(nodes),
            dependencies=tuple(dependencies),
            max_parallel_workers=1,
        )


class MetaPlanner:
    """
    Executive orchestrator planner class (stateless).
    """

    def __init__(self, algorithm: MetaAlgorithm):
        self.algorithm = algorithm

    def plan(self, context: MetaContext) -> MetaSession:
        """
        Generates a validated meta-reasoning session and execution plan.
        """
        state = MetaReasoningState()
        plan = self.algorithm.generate_plan(context, state)

        # Update intermediate state
        state_updated = MetaReasoningState(
            execution_plan=plan,
            optimization_objective_scores=plan.optimization_result,
            diff_from_parent=PolicyDiff(
                source_policy_id=plan.policy_version.policy_id,
                target_policy_id=plan.policy_version.policy_id,
            ),
            facts=state.facts,
        )

        return MetaSession(
            context=context,
            reasoning_state=state_updated,
            policy_version=plan.policy_version,
            execution_lifecycle=ExecutionLifecycle.PLANNED,
        )
