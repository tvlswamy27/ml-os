"""
AdaptivePlanner module computing incremental ExecutionDiff patches for active DAG recovery.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Literal, Set, Dict
from mlos.domain.models.meta_reasoning.execution_schedule import (
    ExecutionSchedule,
    ScheduleNode,
    ScheduleDependency,
)
from mlos.domain.enums.subsystem_name import SubsystemName


@dataclass(frozen=True)
class ExecutionMutation:
    """Incremental topology modification operation."""

    action: Literal["ADD", "REMOVE", "REPLACE"]
    node_id: str
    subsystem: SubsystemName
    dependencies: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionDiff:
    """Collection of topological mutation patches."""

    mutations: List[ExecutionMutation] = field(default_factory=list)


class AdaptivePlanner:
    """
    Computes incremental execution patches and applies mutations to execution plans.
    """

    def replan_diff(
        self, failed_node_id: str, error: Exception, active_schedule: ExecutionSchedule
    ) -> ExecutionDiff:
        """
        Analyze execution failure and construct a minimal ExecutionDiff.
        """
        mutations = []
        # If planning stage fails, replace it with baseline rule planning
        if "plan" in failed_node_id.lower():
            mutations.append(
                ExecutionMutation(
                    action="REPLACE",
                    node_id=failed_node_id,
                    subsystem=SubsystemName.PLANNING,
                )
            )
        # If generation fails, replace with simple rule generation
        elif (
            "generate" in failed_node_id.lower()
            or "generation" in failed_node_id.lower()
        ):
            mutations.append(
                ExecutionMutation(
                    action="REPLACE",
                    node_id=failed_node_id,
                    subsystem=SubsystemName.GENERATION,
                )
            )
        else:
            # Fallback default: replace failed node with the planning subsystem to replan
            mutations.append(
                ExecutionMutation(
                    action="REPLACE",
                    node_id=failed_node_id,
                    subsystem=SubsystemName.PLANNING,
                )
            )
        return ExecutionDiff(mutations=mutations)

    def apply_diff(
        self, schedule: ExecutionSchedule, diff: ExecutionDiff
    ) -> ExecutionSchedule:
        """
        Apply a collection of mutations directly to the active DAG schedule structure.
        """
        nodes_dict: Dict[str, ScheduleNode] = {n.node_id: n for n in schedule.nodes}
        deps_list: List[ScheduleDependency] = list(schedule.dependencies)

        for mutation in diff.mutations:
            node_id = mutation.node_id

            if mutation.action == "REPLACE":
                if node_id in nodes_dict:
                    old_node = nodes_dict[node_id]
                    # Create replaced node
                    new_node = ScheduleNode(
                        node_id=node_id,
                        subsystem=mutation.subsystem,
                        execution_condition=old_node.execution_condition,
                        is_deferred=old_node.is_deferred,
                    )
                    nodes_dict[node_id] = new_node

            elif mutation.action == "REMOVE":
                if node_id in nodes_dict:
                    nodes_dict.pop(node_id)
                # Filter out related dependencies
                deps_list = [
                    d
                    for d in deps_list
                    if d.parent_node_id != node_id and d.child_node_id != node_id
                ]

            elif mutation.action == "ADD":
                new_node = ScheduleNode(
                    node_id=node_id,
                    subsystem=mutation.subsystem,
                    execution_condition="ALWAYS",
                    is_deferred=False,
                )
                nodes_dict[node_id] = new_node
                for parent in mutation.dependencies:
                    if parent in nodes_dict:
                        deps_list.append(
                            ScheduleDependency(
                                parent_node_id=parent,
                                child_node_id=node_id,
                                dependency_type="SEQUENTIAL",
                            )
                        )

        # Validate that the resulting schedule has no cycles
        updated_nodes = tuple(nodes_dict.values())
        updated_deps = tuple(deps_list)

        self.validate_cycle(updated_nodes, updated_deps)

        return ExecutionSchedule(
            nodes=updated_nodes,
            dependencies=updated_deps,
            max_parallel_workers=schedule.max_parallel_workers,
        )

    def validate_cycle(
        self,
        nodes: Tuple[ScheduleNode, ...],
        dependencies: Tuple[ScheduleDependency, ...],
    ) -> None:
        """
        Detect loops / cycle dependencies inside a schedule topology using Kahn's.
        """
        in_degree = {n.node_id: 0 for n in nodes}
        adj: Dict[str, List[str]] = {n.node_id: [] for n in nodes}

        for dep in dependencies:
            if dep.child_node_id in in_degree and dep.parent_node_id in adj:
                adj[dep.parent_node_id].append(dep.child_node_id)
                in_degree[dep.child_node_id] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited = set()

        while queue:
            node = queue.pop(0)
            visited.add(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(visited) != len(nodes):
            raise ValueError(
                "Applying ExecutionDiff patches created a dependency cycle in the schedule!"
            )
