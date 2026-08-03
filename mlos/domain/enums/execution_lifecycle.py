"""
ExecutionLifecycle Enum.

Author: Antigravity
License: MIT
"""

from enum import Enum


class ExecutionLifecycle(Enum):
    """
    Standard lifecycle states for any cognitive subsystem execution node.
    """

    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    RETRIED = "RETRIED"
    COMPLETED = "COMPLETED"
