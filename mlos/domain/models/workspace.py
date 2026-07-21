"""
Workspace domain model.

Represents an ML-OS workspace.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from pathlib import Path

from mlos.domain.models.base import BaseModel


@dataclass
class Workspace(BaseModel):
    """
    Represents the root workspace for ML-OS.
    """

    name: str
    root_path: Path