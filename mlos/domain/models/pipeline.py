"""
Pipeline domain model.

Represents an executable machine learning workflow manifest.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from pathlib import Path

from mlos.domain.models.base import BaseModel


@dataclass
class Pipeline(BaseModel):
    """
    Represents an executable pipeline manifest.
    """

    entrypoint_path: Path

    configuration_path: Path | None = None
