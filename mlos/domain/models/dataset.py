"""
Dataset domain model.

Represents comprehensive metadata discovered about a dataset.

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

    duplicate_rows: int = 0

    unique_values: dict[str, int] = field(default_factory=dict)

    missing_percentages: dict[str, float] = field(default_factory=dict)

    column_types: dict[str, str] = field(default_factory=dict)

    # Extended Dataset Intelligence fields (Milestone 3)
    ordinal_columns: list[str] = field(default_factory=list)

    text_columns: list[str] = field(default_factory=list)

    datetime_columns: list[str] = field(default_factory=list)

    id_columns: list[str] = field(default_factory=list)

    leakage_columns: list[str] = field(default_factory=list)

    high_cardinality_columns: list[str] = field(default_factory=list)

    constant_columns: list[str] = field(default_factory=list)

    near_zero_variance_columns: list[str] = field(default_factory=list)

    skewed_columns: dict[str, float] = field(default_factory=dict)

    imbalance_ratio: float | None = None

    outliers_count: dict[str, int] = field(default_factory=dict)
