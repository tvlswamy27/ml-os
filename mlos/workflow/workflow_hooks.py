"""
Workflow Hooks.

Defines lifecycle hooks and subscription registry for plugins.

Author: Vikram Tanakala
License: MIT
"""

from enum import Enum
from typing import Callable, Any


class WorkflowHook(Enum):
    """
    Available workflow lifecycle hooks.
    """

    BEFORE_ANALYSIS = "before_analysis"
    AFTER_ANALYSIS = "after_analysis"
    BEFORE_FEATURE_INTEL = "before_feature_intel"
    AFTER_FEATURE_INTEL = "after_feature_intel"
    BEFORE_META_REASONING = "before_meta_reasoning"
    AFTER_META_REASONING = "after_meta_reasoning"
    BEFORE_EXECUTION = "before_execution"
    AFTER_EXECUTION = "after_execution"


class HookRegistry:
    """
    Manages event subscription and dispatching for ML-OS lifecycle events.
    """

    def __init__(self):
        self._hooks: dict[WorkflowHook, list[Callable[..., Any]]] = {
            hook: [] for hook in WorkflowHook
        }

    def subscribe(self, hook: WorkflowHook, callback: Callable[..., Any]) -> None:
        """
        Subscribe a plugin hook callback to an execution step.
        """
        self._hooks[hook].append(callback)

    def trigger(self, hook: WorkflowHook, *args, **kwargs) -> None:
        """
        Invoke all registered callbacks for the given hook.
        """
        for callback in self._hooks[hook]:
            callback(*args, **kwargs)
