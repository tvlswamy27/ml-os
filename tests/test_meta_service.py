"""
Integration Tests for MetaService.

Author: Antigravity
License: MIT
"""

import os
from pathlib import Path
import pytest
from mlos.engine.engine import MLOSEngine
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle


def test_meta_service_orchestration():
    engine = MLOSEngine()
    memory = ProjectMemory(project_name="ServiceTestProject", project_goal="ServiceTestGoal")
    engine.project_memory = memory

    # Building context
    context = engine.meta_service.build_context(memory)
    assert context.project_name == "ServiceTestProject"
    assert len(context.provider_registry) == 4

    # Run orchestrate
    session = engine.meta_service.orchestrate_cognition(memory)
    assert session.execution_lifecycle == ExecutionLifecycle.PLANNED
    assert len(memory.meta_sessions) == 1
    assert memory.meta_sessions[0] == session
    assert memory.meta_session == session
