"""
Domain models for the Experiment Tracking System.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RunExecution:
    """Detailed execution telemetry for a specific run."""

    execution_id: UUID
    status: str  # SUCCESS, FAILED
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    stdout: str
    stderr: str
    exit_code: int
    pipeline_hash: str | None = None


@dataclass(frozen=True)
class RunMetrics:
    """Target evaluation metrics logged for a run."""

    metrics_id: UUID
    metrics: dict[str, float]
    timestamp: datetime


@dataclass(frozen=True)
class RunArtifact:
    """Linked registration information pointing to the Central Artifact Registry."""

    artifact_id: UUID
    name: str
    artifact_type: str
    file_path: str
    version: str


@dataclass(frozen=True)
class RunEvent:
    """Audit lifecycle events captured during run execution."""

    event_id: UUID
    event_type: str
    timestamp: datetime
    source: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Snapshot of active system rules/knowledge configurations at execution time."""

    snapshot_id: UUID
    timestamp: datetime
    active_rules_count: int
    rules: list[dict[str, Any]]


@dataclass(frozen=True)
class Run:
    """Single pipeline execution run tracking performance, lineage, and timeline."""

    run_id: UUID
    experiment_id: UUID
    name: str
    timestamp: datetime
    execution: RunExecution
    metrics: RunMetrics
    artifacts: list[RunArtifact]
    events: list[RunEvent]
    knowledge_snapshot: KnowledgeSnapshot
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Experiment:
    """Exploration campaign grouping runs targeting a common objective or project goal."""

    experiment_id: UUID
    name: str
    created_at: datetime
    runs: list[Run] = field(default_factory=list)
