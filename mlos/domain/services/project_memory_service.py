"""
Project Memory Service.
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.evaluation_result import EvaluationResult
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.domain.models.meta_reasoning.meta_session import MetaSession
from mlos.domain.models.meta_reasoning.execution_snapshot import ExecutionSnapshot


class ProjectMemoryService:
    """
    Manages project memory.
    """

    def create(
        self,
        project_name: str,
        project_goal: str,
    ) -> ProjectMemory:

        return ProjectMemory(
            project_name=project_name,
            project_goal=project_goal,
        )

    def update_dataset(
        self,
        memory: ProjectMemory,
        dataset,
    ) -> ProjectMemory:
        """
        Attach dataset information to project memory.
        """

        memory.dataset = dataset

        return memory

    def update_execution_result(
        self,
        memory: ProjectMemory,
        execution_result: ExecutionResult,
    ) -> ProjectMemory:
        """
        Attach execution result to project memory.
        """
        from mlos.domain.models.pipeline_source import PipelineSource

        source = memory.pipeline_source
        if source is None:
            source = PipelineSource(imports="", body="", code="")

        session = ExecutionSession(
            pipeline_source=source,
            status=execution_result.status,
            start_time=execution_result.start_time,
            end_time=execution_result.end_time or execution_result.start_time,
            stdout=execution_result.stdout,
            stderr=execution_result.stderr,
            exit_code=execution_result.exit_code,
            duration_seconds=(
                (
                    execution_result.end_time - execution_result.start_time
                ).total_seconds()
                if execution_result.end_time
                else 0.0
            ),
        )
        return self.add_execution_session(memory, session)

    def add_execution_session(
        self,
        memory: ProjectMemory,
        execution_session: ExecutionSession,
    ) -> ProjectMemory:
        """
        Append execution session to project memory history.
        """
        memory.execution_sessions.append(execution_session)
        return memory

    def update_pipeline(
        self,
        memory: ProjectMemory,
        pipeline: Pipeline,
    ) -> ProjectMemory:
        """
        Attach pipeline reference to project memory.
        """
        memory.pipeline = pipeline
        return memory

    def update_evaluation_result(
        self,
        memory: ProjectMemory,
        evaluation_result: EvaluationResult,
    ) -> ProjectMemory:
        """
        Attach evaluation result to project memory.
        """
        session = EvaluationSession(
            metrics=evaluation_result.metrics,
            checks=evaluation_result.checks,
        )
        return self.add_evaluation_session(memory, session)

    def add_evaluation_session(
        self,
        memory: ProjectMemory,
        evaluation_session: EvaluationSession,
    ) -> ProjectMemory:
        """
        Append evaluation session to project memory history.
        """
        memory.evaluation_sessions.append(evaluation_session)
        return memory

    def add_planning_session(
        self,
        memory: ProjectMemory,
        planning_session: PlanningSession,
    ) -> ProjectMemory:
        """
        Append planning session to project memory.
        """
        memory.planning_sessions.append(planning_session)
        return memory

    def add_reflection_session(
        self,
        memory: ProjectMemory,
        reflection_session: ReflectionSession,
    ) -> ProjectMemory:
        """
        Append reflection session to project memory.
        """
        memory.reflection_sessions.append(reflection_session)
        return memory

    def add_learning_session(
        self,
        memory: ProjectMemory,
        learning_session: LearningSession,
    ) -> ProjectMemory:
        """
        Append learning session to project memory.
        """
        memory.learning_sessions.append(learning_session)
        return memory

    def add_knowledge_session(
        self,
        memory: ProjectMemory,
        knowledge_session: KnowledgeSession,
    ) -> ProjectMemory:
        """
        Append knowledge session to project memory, promote new entries,
        and deprecate older active/experimental entries for the same target component.
        """
        memory.knowledge_sessions.append(knowledge_session)

        for new_entry in knowledge_session.promoted_entries:
            # Find and deprecate superseded entries in the append-only repository
            for old_entry in memory.knowledge_entries:
                if (
                    old_entry.target_component == new_entry.target_component
                    and old_entry.knowledge_type == new_entry.knowledge_type
                    and old_entry.status
                    in (KnowledgeStatus.ACTIVE, KnowledgeStatus.EXPERIMENTAL)
                ):
                    object.__setattr__(old_entry, "status", KnowledgeStatus.DEPRECATED)

            memory.knowledge_entries.append(new_entry)

        return memory

    def update_decisions(
        self,
        memory: ProjectMemory,
        decisions: list[Decision],
    ) -> ProjectMemory:
        """
        Attach decisions to project memory.
        """
        memory.decisions = decisions
        return memory

    def update_generated_codes(
        self,
        memory: ProjectMemory,
        generated_codes: list[GeneratedCode],
    ) -> ProjectMemory:
        """
        Attach generated codes to project memory.
        """
        memory.generated_codes = generated_codes
        return memory

    def update_pipeline_source(
        self,
        memory: ProjectMemory,
        pipeline_source: PipelineSource,
    ) -> ProjectMemory:
        """
        Attach pipeline source to project memory.
        """
        memory.pipeline_source = pipeline_source
        return memory

    def add_feature_session(
        self,
        memory: ProjectMemory,
        feature_session: FeatureSession,
    ) -> ProjectMemory:
        """
        Append feature session to project memory.
        """
        memory.feature_sessions.append(feature_session)
        return memory

    def add_meta_session(
        self,
        memory: ProjectMemory,
        meta_session: MetaSession,
    ) -> ProjectMemory:
        """
        Append meta session to project memory.
        """
        memory.meta_sessions.append(meta_session)
        return memory

    def add_execution_snapshot(
        self,
        memory: ProjectMemory,
        snapshot: ExecutionSnapshot,
    ) -> ProjectMemory:
        """
        Append execution snapshot to project memory.
        """
        memory.execution_snapshots.append(snapshot)
        return memory
