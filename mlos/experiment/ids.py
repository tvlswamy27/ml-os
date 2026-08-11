"""
Experiment ID Generator for ML-OS.

Author: Antigravity
License: MIT
"""

import uuid


def generate_experiment_id() -> str:
    """Generate a unique 8-character experiment identifier."""
    return uuid.uuid4().hex[:8]
