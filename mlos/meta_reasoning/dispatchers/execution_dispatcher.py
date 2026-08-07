"""
ExecutionDispatcher executor module.

Author: Antigravity
License: MIT
"""

import traceback

from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.execution_strategy import ExecutionStrategy
from mlos.meta_reasoning.communication.execution_event_bus import (
    ExecutionEvent,
    ExecutionEventBus,
)


class ExecutionDispatcher:
    """
    Physical execution worker responsible for triggering service calls and reporting statuses.
    """

    def __init__(self, mlos_engine, event_bus: ExecutionEventBus):
        self.mlos_engine = mlos_engine
        self.event_bus = event_bus

    def dispatch_subsystem(
        self, subsystem_name: SubsystemName, strategy: ExecutionStrategy
    ) -> ExecutionLifecycle:
        """
        Executes the subsystem's logic via services or the engine.
        """
        payload = {"subsystem": subsystem_name.value, "strategy": str(strategy)}
        self.event_bus.publish(ExecutionEvent("NodeStarted", payload))

        try:
            memory = self.mlos_engine.project_memory

            if subsystem_name == SubsystemName.PLANNING:
                if (
                    hasattr(self.mlos_engine, "planning_service")
                    and self.mlos_engine.planning_service
                ):
                    self.mlos_engine.planning_service.plan(memory)
                elif hasattr(self.mlos_engine, "plan"):
                    self.mlos_engine.plan()

            elif subsystem_name == SubsystemName.DECISION:
                if (
                    hasattr(self.mlos_engine, "decision_service")
                    and self.mlos_engine.decision_service
                ):
                    self.mlos_engine.decision_service.decide(memory)
                elif (
                    hasattr(self.mlos_engine, "decision_engine")
                    and self.mlos_engine.decision_engine
                ):
                    self.mlos_engine.decision_engine.decide(memory)

            elif subsystem_name == SubsystemName.GENERATION:
                if (
                    hasattr(self.mlos_engine, "generation_service")
                    and self.mlos_engine.generation_service
                ):
                    self.mlos_engine.generation_service.generate(memory)
                elif hasattr(self.mlos_engine, "generate"):
                    self.mlos_engine.generate()

            elif subsystem_name == SubsystemName.ASSEMBLY:
                if hasattr(self.mlos_engine, "assemble"):
                    self.mlos_engine.assemble()

            elif subsystem_name == SubsystemName.EXECUTION:
                if (
                    hasattr(self.mlos_engine, "execution_service")
                    and self.mlos_engine.execution_service
                ):
                    self.mlos_engine.execution_service.execute(memory)
                elif hasattr(self.mlos_engine, "execute"):
                    self.mlos_engine.execute()

            elif subsystem_name == SubsystemName.EVALUATION:
                if (
                    hasattr(self.mlos_engine, "evaluation_service")
                    and self.mlos_engine.evaluation_service
                ):
                    self.mlos_engine.evaluation_service.evaluate(memory)
                elif hasattr(self.mlos_engine, "evaluate"):
                    self.mlos_engine.evaluate()

            elif subsystem_name == SubsystemName.REFLECTION:
                if (
                    hasattr(self.mlos_engine, "reflection_service")
                    and self.mlos_engine.reflection_service
                ):
                    self.mlos_engine.reflection_service.reflect(memory)
                elif hasattr(self.mlos_engine, "reflect"):
                    self.mlos_engine.reflect()

            elif subsystem_name == SubsystemName.LEARNING:
                if (
                    hasattr(self.mlos_engine, "learning_service")
                    and self.mlos_engine.learning_service
                ):
                    self.mlos_engine.learning_service.learn(memory)
                elif hasattr(self.mlos_engine, "learn"):
                    self.mlos_engine.learn()

            elif subsystem_name == SubsystemName.KNOWLEDGE:
                if (
                    hasattr(self.mlos_engine, "knowledge_service")
                    and self.mlos_engine.knowledge_service
                ):
                    self.mlos_engine.knowledge_service.manage(memory)
                elif hasattr(self.mlos_engine, "manage_knowledge"):
                    self.mlos_engine.manage_knowledge()

            self.event_bus.publish(ExecutionEvent("NodeCompleted", payload))
            return ExecutionLifecycle.COMPLETED

        except Exception as e:
            payload["error"] = str(e)
            payload["trace"] = traceback.format_exc()
            self.event_bus.publish(ExecutionEvent("NodeFailed", payload))
            raise e
