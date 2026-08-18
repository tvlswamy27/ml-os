"""
Custom exceptions for the ML-OS execution subsystem.
"""

class ExecutionCancelledError(Exception):
    """Raised when execution is cooperatively cancelled."""
    pass
