"""
Planning Service.

Translates ProjectMemory to PlanningContext and orchestrates the planning flow.

Author: Vikram Tanakala
License: MIT
"""

import json
from datetime import datetime

from mlos.domain.models.planning.goal import Goal
from mlos.domain.models.planning.observation import Observation
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.planning.planning_engine import PlanningEngine


class PlanningService:
    """
    Coordinates building planning contexts, executing algorithms, and persisting results.
    """

    def __init__(
        self,
        planning_engine: PlanningEngine,
        project_memory_service: ProjectMemoryService,
    ):
        """
        Initialize with injected dependencies.
        """
        self.planning_engine = planning_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> PlanningContext:
        """
        Translate ProjectMemory into an immutable PlanningContext.
        """
        goals: list[Goal] = []
        observations: list[Observation] = []

        observed_at = datetime.now()

        # 1. Map project goal
        if memory.project_goal:
            goals.append(
                Goal(
                    name="project_goal",
                    metric="text",
                    target_value=memory.project_goal,
                )
            )

        # 2. Map current stage, completed tasks, and notes if they exist
        if memory.current_stage:
            observations.append(
                Observation(
                    source_subsystem="current_stage",
                    metric_key="stage",
                    metric_value=memory.current_stage,
                    observed_at=observed_at,
                )
            )

        if memory.completed_tasks:
            observations.append(
                Observation(
                    source_subsystem="completed_tasks",
                    metric_key="tasks",
                    metric_value=",".join(memory.completed_tasks),
                    observed_at=observed_at,
                )
            )

        if memory.notes:
            for idx, note in enumerate(memory.notes):
                observations.append(
                    Observation(
                        source_subsystem="notes",
                        metric_key=f"note_{idx}",
                        metric_value=note,
                        observed_at=observed_at,
                    )
                )

        # 3. Map dataset profile
        if memory.dataset is not None:
            ds = memory.dataset
            observations.append(
                Observation(
                    source_subsystem="dataset",
                    metric_key="path",
                    metric_value=str(ds.path),
                    observed_at=observed_at,
                )
            )
            observations.append(
                Observation(
                    source_subsystem="dataset",
                    metric_key="rows",
                    metric_value=str(ds.rows),
                    observed_at=observed_at,
                )
            )
            observations.append(
                Observation(
                    source_subsystem="dataset",
                    metric_key="columns",
                    metric_value=str(ds.columns),
                    observed_at=observed_at,
                )
            )
            if ds.target is not None:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="target",
                        metric_value=str(ds.target),
                        observed_at=observed_at,
                    )
                )
            if ds.problem_type is not None:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="problem_type",
                        metric_value=str(ds.problem_type),
                        observed_at=observed_at,
                    )
                )
            if ds.categorical_columns:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="categorical_columns",
                        metric_value=",".join(ds.categorical_columns),
                        observed_at=observed_at,
                    )
                )
            if ds.numerical_columns:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="numerical_columns",
                        metric_value=",".join(ds.numerical_columns),
                        observed_at=observed_at,
                    )
                )
            if ds.missing_values:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="missing_values",
                        metric_value=json.dumps(ds.missing_values),
                        observed_at=observed_at,
                    )
                )
            observations.append(
                Observation(
                    source_subsystem="dataset",
                    metric_key="duplicate_rows",
                    metric_value=str(ds.duplicate_rows),
                    observed_at=observed_at,
                )
            )
            if ds.unique_values:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="unique_values",
                        metric_value=json.dumps(ds.unique_values),
                        observed_at=observed_at,
                    )
                )
            if ds.missing_percentages:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="missing_percentages",
                        metric_value=json.dumps(ds.missing_percentages),
                        observed_at=observed_at,
                    )
                )
            if ds.column_types:
                observations.append(
                    Observation(
                        source_subsystem="dataset",
                        metric_key="column_types",
                        metric_value=json.dumps(ds.column_types),
                        observed_at=observed_at,
                    )
                )

        # 4. Map project profile
        if memory.project_profile is not None:
            prof = memory.project_profile
            if prof.problem_type is not None:
                observations.append(
                    Observation(
                        source_subsystem="project_profile",
                        metric_key="problem_type",
                        metric_value=str(prof.problem_type),
                        observed_at=observed_at,
                    )
                )
            if prof.complexity is not None:
                observations.append(
                    Observation(
                        source_subsystem="project_profile",
                        metric_key="complexity",
                        metric_value=str(prof.complexity),
                        observed_at=observed_at,
                    )
                )
            if prof.baseline_models:
                observations.append(
                    Observation(
                        source_subsystem="project_profile",
                        metric_key="baseline_models",
                        metric_value=",".join(prof.baseline_models),
                        observed_at=observed_at,
                    )
                )
            if prof.risks:
                for risk in prof.risks:
                    affected_cols = (
                        ",".join(risk.affected_columns) if risk.affected_columns else ""
                    )
                    val = f"severity={risk.severity};description={risk.description};recommendation={risk.recommendation};affected_columns={affected_cols}"
                    observations.append(
                        Observation(
                            source_subsystem="project_profile",
                            metric_key=f"risk:{risk.title}",
                            metric_value=val,
                            observed_at=observed_at,
                        )
                    )

        # 5. Map pipeline reference
        if memory.pipeline is not None:
            pipe = memory.pipeline
            observations.append(
                Observation(
                    source_subsystem="pipeline",
                    metric_key="entrypoint_path",
                    metric_value=str(pipe.entrypoint_path),
                    observed_at=observed_at,
                )
            )
            if pipe.configuration_path is not None:
                observations.append(
                    Observation(
                        source_subsystem="pipeline",
                        metric_key="configuration_path",
                        metric_value=str(pipe.configuration_path),
                        observed_at=observed_at,
                    )
                )

        # 6. Map execution result
        if memory.execution_result is not None:
            exec_res = memory.execution_result
            observations.append(
                Observation(
                    source_subsystem="execution_result",
                    metric_key="status",
                    metric_value=exec_res.status,
                    observed_at=observed_at,
                )
            )
            observations.append(
                Observation(
                    source_subsystem="execution_result",
                    metric_key="start_time",
                    metric_value=str(exec_res.start_time),
                    observed_at=observed_at,
                )
            )
            if exec_res.end_time is not None:
                observations.append(
                    Observation(
                        source_subsystem="execution_result",
                        metric_key="end_time",
                        metric_value=str(exec_res.end_time),
                        observed_at=observed_at,
                    )
                )
            observations.append(
                Observation(
                    source_subsystem="execution_result",
                    metric_key="stdout",
                    metric_value=exec_res.stdout,
                    observed_at=observed_at,
                )
            )
            observations.append(
                Observation(
                    source_subsystem="execution_result",
                    metric_key="stderr",
                    metric_value=exec_res.stderr,
                    observed_at=observed_at,
                )
            )
            if exec_res.exit_code is not None:
                observations.append(
                    Observation(
                        source_subsystem="execution_result",
                        metric_key="exit_code",
                        metric_value=str(exec_res.exit_code),
                        observed_at=observed_at,
                    )
                )

        # 7. Map evaluation result
        if memory.evaluation_result is not None:
            eval_res = memory.evaluation_result
            if eval_res.metrics:
                for k, v in eval_res.metrics.items():
                    observations.append(
                        Observation(
                            source_subsystem="evaluation_result",
                            metric_key=f"metric:{k}",
                            metric_value=str(v),
                            observed_at=observed_at,
                        )
                    )
            if eval_res.checks:
                for k, v in eval_res.checks.items():
                    observations.append(
                        Observation(
                            source_subsystem="evaluation_result",
                            metric_key=f"check:{k}",
                            metric_value=str(v),
                            observed_at=observed_at,
                        )
                    )

        from mlos.domain.models.knowledge_summary import build_knowledge_summary

        return PlanningContext(
            project_name=memory.project_name,
            goals=tuple(goals),
            constraints=(),
            observations=tuple(observations),
            assumptions=(),
            knowledge_summary=build_knowledge_summary(memory),
        )

    def run_planning(self, context: PlanningContext) -> PlanningSession:
        """
        Accept only a PlanningContext, invoke the PlanningEngine, and return a PlanningSession.
        """
        return self.planning_engine.plan(context)

    def plan(self, memory: ProjectMemory) -> PlanningSession:
        """
        Orchestrate the complete planning flow.
        """
        context = self.build_context(memory)
        session = self.run_planning(context)
        self.project_memory_service.add_planning_session(memory, session)
        return session
