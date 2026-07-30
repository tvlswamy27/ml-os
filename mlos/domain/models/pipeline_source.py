"""
Pipeline Source domain model.

Represents the in-memory compiled source of an ML pipeline.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass
from mlos.domain.models.base import BaseModel


@dataclass
class PipelineSource(BaseModel):
    """
    Represents compiled in-memory pipeline blocks.
    """

    imports: str

    body: str

    code: str
