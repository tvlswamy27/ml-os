"""
Project Profile.

Represents the intelligent understanding of a machine learning project.

Author: Vikram Tanakala
License: MIT
"""

from dataclasses import dataclass, field


@dataclass
class ProjectProfile:
    """
    Represents the analyzed profile of a project.
    """

    problem_type: str | None = None

    complexity: str | None = None

    baseline_models: list[str] = field(default_factory=list)

    risks: list[str] = field(default_factory=list)
