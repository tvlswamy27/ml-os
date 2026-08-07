"""
ExecutionSession domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from mlos.domain.models.pipeline_source import PipelineSource


@dataclass(frozen=True)
class ExecutionSession:
    """
    Represents the immutable execution results of an ML pipeline run.
    """

    pipeline_source: PipelineSource

    status: str

    start_time: datetime

    end_time: datetime

    stdout: str = ""

    stderr: str = ""

    exit_code: int | None = None

    duration_seconds: float = 0.0

    artifacts: dict[str, str] = field(default_factory=dict)

    model_path: str | None = None

    metrics_path: str | None = None

    pipeline_hash: str | None = None

    id: UUID = field(default_factory=uuid4, init=False)

    version: str = field(default="2.0.0", init=False)

    created_at: datetime = field(default_factory=datetime.now, init=False)

    updated_at: datetime = field(default_factory=datetime.now, init=False)

    def to_dict(self) -> dict:
        data = asdict(self)

        data["id"] = str(self.id)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()

        return data
