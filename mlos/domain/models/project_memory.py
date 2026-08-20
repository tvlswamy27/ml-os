"""
Project Memory.

Stores everything ML-OS knows about a project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.decision import Decision
from mlos.domain.models.evaluation_result import EvaluationResult
from mlos.domain.models.evaluation_session import EvaluationSession
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.execution_session import ExecutionSession
from mlos.domain.models.feature_intelligence.feature_session import FeatureSession
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.meta_reasoning.execution_snapshot import ExecutionSnapshot
from mlos.domain.models.meta_reasoning.meta_session import MetaSession
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_profile import ProjectProfile
from mlos.domain.models.reflection.reflection_session import ReflectionSession


@dataclass
class ProjectMemory(BaseModel):
    """
    Stores project knowledge.
    """

    project_name: str

    project_goal: str

    dataset: Dataset | None = None

    current_stage: str = "Project Initialization"

    run_id: str | None = None

    completed_stages: list[str] = field(default_factory=list)

    completed_tasks: list[str] = field(default_factory=list)

    notes: list[str] = field(default_factory=list)

    project_profile: ProjectProfile | None = None

    pipeline: Pipeline | None = None

    planning_sessions: list[PlanningSession] = field(default_factory=list)

    decisions: list[Decision] = field(default_factory=list)

    generated_codes: list[GeneratedCode] = field(default_factory=list)

    pipeline_source: PipelineSource | None = None

    execution_sessions: list[ExecutionSession] = field(default_factory=list)

    evaluation_sessions: list[EvaluationSession] = field(default_factory=list)

    reflection_sessions: list[ReflectionSession] = field(default_factory=list)

    learning_sessions: list[LearningSession] = field(default_factory=list)

    knowledge_sessions: list[KnowledgeSession] = field(default_factory=list)

    knowledge_entries: list[KnowledgeEntry] = field(default_factory=list)

    feature_sessions: list[FeatureSession] = field(default_factory=list)

    meta_sessions: list[MetaSession] = field(default_factory=list)

    execution_snapshots: list[ExecutionSnapshot] = field(default_factory=list)

    @property
    def evaluation_result(self) -> EvaluationResult | None:
        """
        Backward compatible access to the latest evaluation result.
        """
        if not self.evaluation_sessions:
            return None
        latest = self.evaluation_sessions[-1]
        return EvaluationResult(
            metrics=latest.metrics,
            checks=latest.checks,
        )

    @evaluation_result.setter
    def evaluation_result(self, value: EvaluationResult | None) -> None:
        """
        Backward compatible setter that appends translated EvaluationSession.
        """
        if value is None:
            self.evaluation_sessions.clear()
            return
        session = EvaluationSession(
            metrics=value.metrics,
            checks=value.checks,
        )
        self.evaluation_sessions.append(session)

    @property
    def execution_result(self) -> ExecutionResult | None:
        """
        Backward compatible access to the latest execution result.
        """
        if not self.execution_sessions:
            return None
        latest = self.execution_sessions[-1]
        return ExecutionResult(
            status=latest.status,
            start_time=latest.start_time,
            end_time=latest.end_time,
            stdout=latest.stdout,
            stderr=latest.stderr,
            exit_code=latest.exit_code,
        )

    @execution_result.setter
    def execution_result(self, value: ExecutionResult | None) -> None:
        """
        Backward compatible setter that appends translated ExecutionSession.
        """
        if value is None:
            self.execution_sessions.clear()
            return
        from mlos.domain.models.execution_session import ExecutionSession
        from mlos.domain.models.pipeline_source import PipelineSource

        session = ExecutionSession(
            pipeline_source=self.pipeline_source
            or PipelineSource(imports="", body="", code=""),
            status=value.status,
            start_time=value.start_time,
            end_time=value.end_time or value.start_time,
            stdout=value.stdout,
            stderr=value.stderr,
            exit_code=value.exit_code,
            duration_seconds=(
                (value.end_time - value.start_time).total_seconds()
                if value.end_time
                else 0.0
            ),
        )
        self.execution_sessions.append(session)

    @property
    def reflection_session(self) -> ReflectionSession | None:
        """
        Backward compatible access to the latest reflection session.
        """
        if not self.reflection_sessions:
            return None
        return self.reflection_sessions[-1]

    @reflection_session.setter
    def reflection_session(self, value: ReflectionSession | None) -> None:
        """
        Backward compatible setter that appends translated ReflectionSession.
        """
        if value is None:
            self.reflection_sessions.clear()
            return
        self.reflection_sessions.append(value)

    @property
    def learning_session(self) -> LearningSession | None:
        """
        Backward compatible access to the latest learning session.
        """
        if not self.learning_sessions:
            return None
        return self.learning_sessions[-1]

    @learning_session.setter
    def learning_session(self, value: LearningSession | None) -> None:
        """
        Backward compatible setter that appends translated LearningSession.
        """
        if value is None:
            self.learning_sessions.clear()
            return
        self.learning_sessions.append(value)

    @property
    def knowledge_session(self) -> KnowledgeSession | None:
        """
        Backward compatible access to the latest knowledge session.
        """
        if not self.knowledge_sessions:
            return None
        return self.knowledge_sessions[-1]

    @knowledge_session.setter
    def knowledge_session(self, value: KnowledgeSession | None) -> None:
        """
        Backward compatible setter that appends translated KnowledgeSession.
        """
        if value is None:
            self.knowledge_sessions.clear()
            return
        self.knowledge_sessions.append(value)

    @property
    def feature_session(self) -> FeatureSession | None:
        """
        Backward compatible access to the latest feature session.
        """
        if not self.feature_sessions:
            return None
        return self.feature_sessions[-1]

    @feature_session.setter
    def feature_session(self, value: FeatureSession | None) -> None:
        """
        Backward compatible setter that appends FeatureSession.
        """
        if value is None:
            self.feature_sessions.clear()
            return
        self.feature_sessions.append(value)

    @property
    def meta_session(self) -> MetaSession | None:
        """
        Access to the latest meta session.
        """
        if not self.meta_sessions:
            return None
        return self.meta_sessions[-1]

    @meta_session.setter
    def meta_session(self, value: MetaSession | None) -> None:
        """
        Setter that appends MetaSession.
        """
        if value is None:
            self.meta_sessions.clear()
            return
        self.meta_sessions.append(value)
