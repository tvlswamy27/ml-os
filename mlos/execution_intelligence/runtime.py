"""
ExecutionRuntime and ExecutionGraph topologically sorting and running execution stages.

Author: Antigravity
License: MIT
"""

from typing import Dict, List, Set, Any
from mlos.domain.models.project_memory import ProjectMemory
from mlos.execution_intelligence.stage import ExecutionStage


class ExecutionGraph:
    """
    Topological scheduling graph representing the dependency structure of execution stages.
    """

    def __init__(self) -> None:
        self.stages: Dict[str, ExecutionStage] = {}
        # node_id -> parent_node_ids (dependencies list)
        self.dependencies: Dict[str, List[str]] = {}

    def add_stage(self, stage: ExecutionStage) -> None:
        """Register a stage in the graph."""
        self.stages[stage.name] = stage
        if stage.name not in self.dependencies:
            self.dependencies[stage.name] = []

    def add_dependency(self, child_name: str, parent_name: str) -> None:
        """Declare that child_name depends on parent_name executing first."""
        if child_name not in self.stages:
            raise ValueError(f"Stage '{child_name}' is not registered in the graph.")
        if parent_name not in self.stages:
            raise ValueError(f"Stage '{parent_name}' is not registered in the graph.")
        self.dependencies[child_name].append(parent_name)

    def topological_sort(self) -> List[str]:
        """
        Sort the stages topologically using Kahn's algorithm.
        Detects dependency cycles.
        """
        in_degree: Dict[str, int] = {name: 0 for name in self.stages}
        adj: Dict[str, List[str]] = {name: [] for name in self.stages}

        for child, parents in self.dependencies.items():
            for p in parents:
                adj[p].append(child)
                in_degree[child] += 1

        # Queue contains nodes with in-degree 0
        queue = [name for name, deg in in_degree.items() if deg == 0]
        topo_order: List[str] = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(self.stages):
            raise ValueError("Dependency cycle detected in the execution graph!")

        return topo_order


class ExecutionRuntime:
    """
    Runtime engine responsible for orchestrating stage executions.
    """

    def run_graph(
        self,
        graph: ExecutionGraph,
        memory: ProjectMemory,
        dataset_path: str,
        target: str,
        project_path: str | None = None,
    ) -> Dict[str, Any]:
        """
        Sort and run the stages topologically, sharing context and notifying the Event Bus.
        """
        from mlos.communication.event_bus import GlobalEventBus

        event_bus = GlobalEventBus()
        topo_order = graph.topological_sort()

        # Shared execution context across stages
        context: Dict[str, Any] = {
            "dataset_path": dataset_path,
            "target_column": target,
            "project_path": project_path,
        }
        results: Dict[str, Any] = {}

        event_bus.publish(
            event_type="ExecutionStarted",
            source="ExecutionRuntime",
            payload={"project_name": memory.project_name, "stages": topo_order},
        )

        for name in topo_order:
            stage = graph.stages[name]

            event_bus.publish(
                event_type="StageStarted",
                source="ExecutionRuntime",
                payload={"stage": name},
            )

            try:
                result = stage.execute(memory, context)
                results[name] = result

                event_bus.publish(
                    event_type="StageCompleted",
                    source="ExecutionRuntime",
                    payload={
                        "stage": name,
                        "status": "SUCCESS",
                        "details": str(result),
                    },
                )
            except Exception as e:
                event_bus.publish(
                    event_type="StageFailed",
                    source="ExecutionRuntime",
                    payload={"stage": name, "status": "FAILED", "error": str(e)},
                )

                event_bus.publish(
                    event_type="ExecutionFailed",
                    source="ExecutionRuntime",
                    payload={
                        "project_name": memory.project_name,
                        "failed_stage": name,
                        "error": str(e),
                    },
                )
                raise e

        # Collect metrics, artifacts and update memory fields for backward compatibility
        if "evaluation_metrics" in context:
            from mlos.domain.models.evaluation_result import EvaluationResult

            metrics = context["evaluation_metrics"]
            memory.evaluation_result = EvaluationResult(
                metrics=metrics,
                checks={k: True for k in metrics},
            )

        event_bus.publish(
            event_type="ExecutionCompleted",
            source="ExecutionRuntime",
            payload={"project_name": memory.project_name},
        )

        # Store context in results dict for downstream extraction of artifacts/metrics
        results["__context__"] = context
        return results
