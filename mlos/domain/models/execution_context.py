"""
ExecutionContext domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass

from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.project_memory import ProjectMemory


@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable input context for the Execution Engine.
    """

    project_memory: ProjectMemory
    pipeline_source: PipelineSource
