"""
Dataset domain model.

Represents information discovered about a dataset.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.base import BaseModel


@dataclass
class Dataset(BaseModel):
    """
    Stores metadata about a dataset.
    """

    path: str

    rows: int = 0

    columns: int = 0

    target: str | None = None

    problem_type: str | None = None

    categorical_columns: list[str] = field(default_factory=list)

    numerical_columns: list[str] = field(default_factory=list)

    missing_values: dict[str, int] = field(default_factory=dict)