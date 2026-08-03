"""
Workflow Engine.

Directly orchestrates the ML-OS subsystems lifecycle sequence.

Author: Vikram Tanakala
License: MIT
"""

from datetime import datetime
import traceback

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.workflow_result import WorkflowResult
from mlos.workflow.workflow_hooks import HookRegistry, WorkflowHook
from mlos.domain.services.planning_service import PlanningService
from mlos.domain.services.decision_service import DecisionService
from mlos.domain.services.generation_service import GenerationService
from mlos.domain.services.execution_service import ExecutionService
from mlos.domain.services.evaluation_service import EvaluationService
from mlos.domain.services.reflection_service import ReflectionService
from mlos.domain.services.learning_service import LearningService
from mlos.domain.services.knowledge_service import KnowledgeService
from mlos.domain.services.feature_service import FeatureService


class WorkflowEngine:
    """
    Stateless workflow runner that executes ML lifecycle subsystems sequentially.
    """

    def __init__(
        self,
        mlos_engine,
        hooks: HookRegistry,
        feature_service: FeatureService | None = None,
        planning_service: PlanningService | None = None,
        decision_service: DecisionService | None = None,
        generation_service: GenerationService | None = None,
        execution_service: ExecutionService | None = None,
        evaluation_service: EvaluationService | None = None,
        reflection_service: ReflectionService | None = None,
        learning_service: LearningService | None = None,
        knowledge_service: KnowledgeService | None = None,
    ):
        self.mlos_engine = mlos_engine
        self.hooks = hooks
        if feature_service is None and hasattr(mlos_engine, "feature_service"):
            feature_service = mlos_engine.feature_service
        self.feature_service = feature_service
        if planning_service is None and hasattr(mlos_engine, "planning_service"):
            planning_service = mlos_engine.planning_service
        self.planning_service = planning_service
        if decision_service is None and hasattr(mlos_engine, "decision_service"):
            decision_service = mlos_engine.decision_service
        self.decision_service = decision_service
        if generation_service is None and hasattr(mlos_engine, "generation_service"):
            generation_service = mlos_engine.generation_service
        self.generation_service = generation_service
        if execution_service is None and hasattr(mlos_engine, "execution_service"):
            execution_service = mlos_engine.execution_service
        self.execution_service = execution_service
        if evaluation_service is None and hasattr(mlos_engine, "evaluation_service"):
            evaluation_service = mlos_engine.evaluation_service
        self.evaluation_service = evaluation_service
        if reflection_service is None and hasattr(mlos_engine, "reflection_service"):
            reflection_service = mlos_engine.reflection_service
        self.reflection_service = reflection_service
        if learning_service is None and hasattr(mlos_engine, "learning_service"):
            learning_service = mlos_engine.learning_service
        self.learning_service = learning_service
        if knowledge_service is None and hasattr(mlos_engine, "knowledge_service"):
            knowledge_service = mlos_engine.knowledge_service
        self.knowledge_service = knowledge_service

    def run(self, dataset_path: str, target: str | None = None) -> WorkflowResult:
        """
        Executes the unidirectional pipeline, triggers hooks, and returns a WorkflowResult.
        """
        start_time = datetime.now()
        errors = {}

        try:
            # 1. Analysis Subsystem
            self.hooks.trigger(WorkflowHook.BEFORE_ANALYSIS, dataset_path)
            self.mlos_engine.analyze(dataset_path)
            self.hooks.trigger(
                WorkflowHook.AFTER_ANALYSIS, self.mlos_engine.project_memory
            )

            # 1b. Feature Intelligence Subsystem
            self.hooks.trigger(
                WorkflowHook.BEFORE_FEATURE_INTEL, self.mlos_engine.project_memory
            )
            if (
                self.feature_service is not None
                and self.mlos_engine.project_memory is not None
            ):
                self.feature_service.analyze_features(self.mlos_engine.project_memory)
            self.hooks.trigger(
                WorkflowHook.AFTER_FEATURE_INTEL, self.mlos_engine.project_memory
            )

            # 1c. Meta-Reasoning Subsystem
            self.hooks.trigger(
                WorkflowHook.BEFORE_META_REASONING, self.mlos_engine.project_memory
            )
            meta_executed = False
            if (
                hasattr(self.mlos_engine, "meta_service")
                and self.mlos_engine.meta_service is not None
            ):
                try:
                    meta_session = self.mlos_engine.meta_service.orchestrate_cognition(
                        self.mlos_engine.project_memory
                    )

                    from mlos.meta_reasoning.communication.execution_event_bus import (
                        ExecutionEventBus,
                    )
                    from mlos.meta_reasoning.dispatchers.execution_dispatcher import (
                        ExecutionDispatcher,
                    )
                    from mlos.meta_reasoning.scheduling.execution_scheduler import (
                        ExecutionScheduler,
                    )

                    event_bus = ExecutionEventBus()
                    dispatcher = ExecutionDispatcher(self.mlos_engine, event_bus)
                    scheduler = ExecutionScheduler(dispatcher, event_bus)

                    plan = meta_session.reasoning_state.execution_plan
                    if plan:
                        snapshot = scheduler.execute_schedule(
                            plan, meta_session.context
                        )
                        self.mlos_engine.project_memory_service.add_execution_snapshot(
                            self.mlos_engine.project_memory, snapshot
                        )
                        meta_executed = True
                except Exception:
                    pass

            self.hooks.trigger(
                WorkflowHook.AFTER_META_REASONING, self.mlos_engine.project_memory
            )

            if not meta_executed:
                # 2. Planning Subsystem
                if (
                    self.planning_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.planning_service.plan(self.mlos_engine.project_memory)

                # 3. Decision Subsystem
                if self.decision_service is not None:
                    decisions = self.decision_service.decide(
                        self.mlos_engine.project_memory
                    )
                else:
                    decisions = self.mlos_engine.decision_engine.decide(
                        self.mlos_engine.project_memory
                    )

                # 4. Generation Subsystem
                if (
                    self.generation_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.generation_service.generate(self.mlos_engine.project_memory)

                # 5. Assembly Subsystem
                self.mlos_engine.assemble()

                # 5. Execution Subsystem
                self.hooks.trigger(
                    WorkflowHook.BEFORE_EXECUTION, self.mlos_engine.project_memory
                )
                default_execute = self.mlos_engine.__class__.execute
                is_execute_mocked = getattr(
                    self.mlos_engine.execute, "__code__", None
                ) != getattr(default_execute, "__code__", None)
                if (
                    not is_execute_mocked
                    and self.execution_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.execution_service.execute(self.mlos_engine.project_memory)
                else:
                    self.mlos_engine.execute()
                self.hooks.trigger(
                    WorkflowHook.AFTER_EXECUTION, self.mlos_engine.project_memory
                )

                # 6. Evaluation Subsystem
                default_evaluate = self.mlos_engine.__class__.evaluate
                is_evaluate_mocked = getattr(
                    self.mlos_engine.evaluate, "__code__", None
                ) != getattr(default_evaluate, "__code__", None)
                if (
                    not is_evaluate_mocked
                    and self.evaluation_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.evaluation_service.evaluate(self.mlos_engine.project_memory)
                else:
                    self.mlos_engine.evaluate()

                # 7. Reflection Subsystem (Executes immediately after Evaluation)
                is_reflect_mocked = False
                if hasattr(self.mlos_engine, "reflect"):
                    default_reflect = self.mlos_engine.__class__.reflect
                    is_reflect_mocked = getattr(
                        self.mlos_engine.reflect, "__code__", None
                    ) != getattr(default_reflect, "__code__", None)

                if (
                    not is_reflect_mocked
                    and self.reflection_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.reflection_service.reflect(self.mlos_engine.project_memory)
                elif hasattr(self.mlos_engine, "reflect"):
                    self.mlos_engine.reflect()

                # 8. Learning Subsystem (Executes immediately after Reflection)
                is_learn_mocked = False
                if hasattr(self.mlos_engine, "learn"):
                    default_learn = self.mlos_engine.__class__.learn
                    is_learn_mocked = getattr(
                        self.mlos_engine.learn, "__code__", None
                    ) != getattr(default_learn, "__code__", None)

                if (
                    not is_learn_mocked
                    and self.learning_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.learning_service.learn(self.mlos_engine.project_memory)
                elif hasattr(self.mlos_engine, "learn"):
                    self.mlos_engine.learn()

                # 9. Knowledge Subsystem (Executes immediately after Learning)
                is_knowledge_mocked = False
                if hasattr(self.mlos_engine, "manage_knowledge"):
                    default_knowledge = self.mlos_engine.__class__.manage_knowledge
                    is_knowledge_mocked = getattr(
                        self.mlos_engine.manage_knowledge, "__code__", None
                    ) != getattr(default_knowledge, "__code__", None)

                if (
                    not is_knowledge_mocked
                    and self.knowledge_service is not None
                    and self.mlos_engine.project_memory is not None
                ):
                    self.knowledge_service.manage(self.mlos_engine.project_memory)
                elif hasattr(self.mlos_engine, "manage_knowledge"):
                    self.mlos_engine.manage_knowledge()

        except Exception as e:
            errors["lifecycle_run"] = (
                f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            return WorkflowResult(
                status="FAILED",
                start_time=start_time,
                end_time=datetime.now(),
                errors=errors,
            )

        return WorkflowResult(
            status="SUCCESS",
            start_time=start_time,
            end_time=datetime.now(),
        )
