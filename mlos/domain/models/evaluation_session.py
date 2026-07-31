"""
EvaluationSession domain model.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EvaluationSession:
    """
    Represents the immutable evaluation results of an ML pipeline run.
    """

    metrics: dict[str, float] = field(default_factory=dict)

    checks: dict[str, bool] = field(default_factory=dict)

    status: str = "SUCCESS"

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
