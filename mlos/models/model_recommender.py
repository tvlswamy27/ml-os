"""
Model Recommendation Engine for ML-OS.

Ranks models based on dataset characteristics, task suitability, resource budgets,
and user preferences.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from mlos.domain.models.dataset import Dataset
from mlos.models.catalog import ModelCatalog, ModelMetadata, TaskType


@dataclass
class ModelRecommendation:
    """Ranked model recommendation output."""

    model_id: str
    name: str
    rank: int
    suitability_score: float
    reasoning: list[str] = field(default_factory=list)
    rejection_reason: str | None = None
    is_available: bool = True
    metadata: ModelMetadata | None = None


class ModelRecommender:
    """
    Evaluates candidate models from ModelCatalog against dataset characteristics.
    """

    def recommend(
        self,
        dataset: Dataset,
        max_memory_mb: float = 4096.0,
        max_training_seconds: float = 600.0,
        interpretability_weight: float = 0.5,
        speed_weight: float = 0.5,
    ) -> list[ModelRecommendation]:
        """
        Rank all models for a given dataset and problem type.
        """
        task_type = dataset.problem_type or "binary_classification"
        # Standardize task type mapping
        if "classification" in task_type:
            target_task = TaskType.CLASSIFICATION
        elif "regression" in task_type:
            target_task = TaskType.REGRESSION
        elif "clustering" in task_type:
            target_task = TaskType.CLUSTERING
        elif "forecasting" in task_type or "time_series" in task_type:
            target_task = TaskType.FORECASTING
        else:
            target_task = TaskType.CLASSIFICATION

        all_models = ModelCatalog.list_for_task(target_task)
        recommendations: list[ModelRecommendation] = []

        for meta in all_models:
            reasoning = []
            score = 100.0
            rejection_reason = None
            is_avail = meta.is_available()

            if not is_avail:
                rejection_reason = (
                    f"Library '{meta.module_path}' is not installed in the environment."
                )
                recommendations.append(
                    ModelRecommendation(
                        model_id=meta.model_id,
                        name=meta.name,
                        rank=999,
                        suitability_score=0.0,
                        reasoning=[rejection_reason],
                        rejection_reason=rejection_reason,
                        is_available=False,
                        metadata=meta,
                    )
                )
                continue

            # Check dataset size constraints
            if dataset.rows < meta.recommended_min_samples:
                score -= 30.0
                reasoning.append(
                    f"Dataset rows ({dataset.rows}) below recommended min ({meta.recommended_min_samples})."
                )
            elif dataset.rows > meta.recommended_max_samples:
                score -= 40.0
                reasoning.append(
                    f"Dataset rows ({dataset.rows}) exceeds recommended max ({meta.recommended_max_samples})."
                )

            # Check missing values
            has_missing = any(v > 0 for v in dataset.missing_values.values())
            if has_missing and not meta.handles_missing_values:
                score -= 15.0
                reasoning.append("Model requires pre-imputation for missing values.")
            elif has_missing and meta.handles_missing_values:
                score += 10.0
                reasoning.append("Native missing value handling supported.")

            # Check high cardinality
            if len(dataset.high_cardinality_columns) > 0 and meta.handles_categorical:
                score += 10.0
                reasoning.append(
                    "Native categorical feature handling suited for high-cardinality columns."
                )

            # Check class imbalance
            if dataset.imbalance_ratio and dataset.imbalance_ratio > 3.0:
                if "boost" in meta.model_id or "forest" in meta.model_id:
                    score += 10.0
                    reasoning.append(
                        f"Ensemble tree structure handles class imbalance ratio ({dataset.imbalance_ratio}:1)."
                    )

            # Apply interpretability and speed weights
            interp_contrib = meta.interpretability_score * 5.0 * interpretability_weight
            speed_contrib = meta.estimated_training_speed * 5.0 * speed_weight
            score += interp_contrib + speed_contrib

            if meta.interpretability_score >= 8:
                reasoning.append(
                    f"High model interpretability score ({meta.interpretability_score}/10)."
                )

            reasoning.append(f"Base suitability score: {round(score, 1)}.")

            recommendations.append(
                ModelRecommendation(
                    model_id=meta.model_id,
                    name=meta.name,
                    rank=0,
                    suitability_score=round(max(score, 1.0), 1),
                    reasoning=reasoning,
                    is_available=True,
                    metadata=meta,
                )
            )

        # Sort recommendations by suitability score descending
        avail_recs = [r for r in recommendations if r.is_available]
        unavail_recs = [r for r in recommendations if not r.is_available]

        avail_recs.sort(key=lambda r: r.suitability_score, reverse=True)
        for i, rec in enumerate(avail_recs, start=1):
            rec.rank = i

        return avail_recs + unavail_recs
