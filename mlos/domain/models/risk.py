from dataclasses import dataclass

from mlos.domain.models.base import BaseModel


@dataclass
class Risk(BaseModel):
    """
    Represents a project risk detected by ML-OS.
    """

    title: str

    severity: str

    description: str

    recommendation: str = ""

    affected_columns: list[str] | None = None
