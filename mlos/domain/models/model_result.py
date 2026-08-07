"""
ModelResult domain model storing comprehensive evaluation & training outcomes.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResult:
    """Dataclass encapsulating execution results of a trained model candidate."""

    model_id: str
    model_name: str
    status: str = "SUCCESS"  # "SUCCESS", "SKIPPED", "FAILED"
    metrics: dict[str, float] = field(default_factory=dict)
    cv_scores: list[float] = field(default_factory=list)
    cv_mean: float = 0.0
    cv_std: float = 0.0
    training_time: float = 0.0
    prediction_time: float = 0.0
    memory_usage_mb: float = 0.0
    feature_importance: dict[str, float] = field(default_factory=dict)
    explainability_method: str = "none"
    hpo_result: dict[str, Any] = field(default_factory=dict)
    model_size_bytes: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    model_object: Any | None = None
    fitted_preprocessor: Any | None = None
