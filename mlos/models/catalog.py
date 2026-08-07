"""
Plugin-based Model Catalog and Capability Registration Engine for ML-OS.

Author: Antigravity
License: MIT
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class ModelMetadata:
    """Rich capability metadata for catalog model plugins."""

    model_id: str
    name: str
    supported_tasks: list[TaskType]
    handles_missing_values: bool = False
    handles_categorical: bool = False
    supports_sparse: bool = False
    supports_multiclass: bool = True
    supports_multilabel: bool = False
    supports_gpu: bool = False
    supports_probability: bool = True
    supports_feature_importance: bool = False
    supports_shap: bool = False
    supports_hpo: bool = True
    supports_partial_fit: bool = False
    supports_online_learning: bool = False
    estimated_memory_mb: float = 50.0
    estimated_training_speed: int = 5  # 1 (slowest) to 10 (fastest)
    estimated_prediction_speed: int = 5
    interpretability_score: int = 5  # 1 to 10
    recommended_min_samples: int = 10
    recommended_max_samples: int = 10_000_000
    recommended_max_features: int = 100_000
    module_path: str = ""
    class_name: str = ""
    default_parameters: dict[str, Any] = field(default_factory=dict)
    hpo_param_space: dict[str, Any] = field(default_factory=dict)
    factory_fn: Callable[..., Any] | None = None

    def is_available(self) -> bool:
        """Check if the model's underlying library is installed."""
        if not self.module_path or not self.class_name:
            return True
        try:
            mod = __import__(self.module_path, fromlist=[self.class_name])
            getattr(mod, self.class_name)
            return True
        except (ImportError, AttributeError):
            return False


class ModelCatalog:
    """Centralized plugin registry for all ML-OS supported models."""

    _registry: dict[str, ModelMetadata] = {}

    @classmethod
    def register(cls, metadata: ModelMetadata) -> None:
        """Register a model plugin into the catalog."""
        cls._registry[metadata.model_id] = metadata

    @classmethod
    def get(cls, model_id: str) -> ModelMetadata | None:
        """Retrieve model metadata by ID."""
        return cls._registry.get(model_id)

    @classmethod
    def list_all(cls) -> list[ModelMetadata]:
        """List all registered model metadata."""
        return list(cls._registry.values())

    @classmethod
    def list_for_task(cls, task_type: TaskType | str) -> list[ModelMetadata]:
        """List available models suited for a given task type."""
        task_str = (
            task_type.value if isinstance(task_type, TaskType) else str(task_type)
        )
        return [
            m
            for m in cls._registry.values()
            if any(t.value == task_str for t in m.supported_tasks)
        ]


# ---------------------------------------------------------
# Default Model Registrations (Classification)
# ---------------------------------------------------------
ModelCatalog.register(
    ModelMetadata(
        model_id="logistic_regression",
        name="Logistic Regression",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        supports_feature_importance=True,  # coefficients
        interpretability_score=9,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="sklearn.linear_model",
        class_name="LogisticRegression",
        default_parameters={"max_iter": 1000, "random_state": 42},
        hpo_param_space={"C": [0.01, 0.1, 1.0, 10.0], "solver": ["lbfgs", "liblinear"]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="random_forest_classifier",
        name="Random Forest Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=7,
        estimated_training_speed=6,
        estimated_prediction_speed=8,
        module_path="sklearn.ensemble",
        class_name="RandomForestClassifier",
        default_parameters={"n_estimators": 100, "random_state": 42},
        hpo_param_space={
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20],
            "min_samples_split": [2, 5],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="extra_trees_classifier",
        name="Extra Trees Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=7,
        estimated_training_speed=7,
        estimated_prediction_speed=8,
        module_path="sklearn.ensemble",
        class_name="ExtraTreesClassifier",
        default_parameters={"n_estimators": 100, "random_state": 42},
        hpo_param_space={"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="decision_tree_classifier",
        name="Decision Tree Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        supports_feature_importance=True,
        interpretability_score=10,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="sklearn.tree",
        class_name="DecisionTreeClassifier",
        default_parameters={"random_state": 42},
        hpo_param_space={
            "max_depth": [None, 5, 10, 15],
            "criterion": ["gini", "entropy"],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="gradient_boosting_classifier",
        name="Gradient Boosting Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=False,
        supports_multiclass=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=4,
        estimated_prediction_speed=7,
        module_path="sklearn.ensemble",
        class_name="GradientBoostingClassifier",
        default_parameters={"n_estimators": 100, "random_state": 42},
        hpo_param_space={
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1, 0.2],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="knn_classifier",
        name="K-Nearest Neighbors Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        interpretability_score=5,
        estimated_training_speed=9,
        estimated_prediction_speed=4,
        module_path="sklearn.neighbors",
        class_name="KNeighborsClassifier",
        default_parameters={"n_neighbors": 5},
        hpo_param_space={
            "n_neighbors": [3, 5, 7, 9],
            "weights": ["uniform", "distance"],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="svc",
        name="Support Vector Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_multiclass=True,
        supports_probability=True,
        interpretability_score=4,
        estimated_training_speed=3,
        estimated_prediction_speed=5,
        module_path="sklearn.svm",
        class_name="SVC",
        default_parameters={"probability": True, "random_state": 42},
        hpo_param_space={"C": [0.1, 1.0, 10.0], "kernel": ["rbf", "linear"]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="gaussian_nb",
        name="Gaussian Naive Bayes",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=False,
        supports_multiclass=True,
        supports_probability=True,
        interpretability_score=8,
        estimated_training_speed=10,
        estimated_prediction_speed=10,
        module_path="sklearn.naive_bayes",
        class_name="GaussianNB",
        default_parameters={},
    )
)

# Optional Advanced Gradient Boosters
ModelCatalog.register(
    ModelMetadata(
        model_id="xgboost_classifier",
        name="XGBoost Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=True,
        handles_categorical=True,
        supports_sparse=True,
        supports_multiclass=True,
        supports_gpu=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=8,
        estimated_prediction_speed=9,
        module_path="xgboost",
        class_name="XGBClassifier",
        default_parameters={
            "n_estimators": 100,
            "random_state": 42,
            "eval_metric": "logloss",
        },
        hpo_param_space={
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1, 0.2],
            "max_depth": [3, 6, 9],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="lightgbm_classifier",
        name="LightGBM Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=True,
        handles_categorical=True,
        supports_sparse=True,
        supports_multiclass=True,
        supports_gpu=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="lightgbm",
        class_name="LGBMClassifier",
        default_parameters={"n_estimators": 100, "random_state": 42, "verbose": -1},
        hpo_param_space={
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1],
            "num_leaves": [31, 63],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="catboost_classifier",
        name="CatBoost Classifier",
        supported_tasks=[TaskType.CLASSIFICATION],
        handles_missing_values=True,
        handles_categorical=True,
        supports_sparse=False,
        supports_multiclass=True,
        supports_gpu=True,
        supports_probability=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=7,
        estimated_prediction_speed=9,
        module_path="catboost",
        class_name="CatBoostClassifier",
        default_parameters={"iterations": 100, "random_seed": 42, "verbose": 0},
        hpo_param_space={
            "iterations": [50, 100, 200],
            "learning_rate": [0.03, 0.1],
            "depth": [4, 6, 8],
        },
    )
)

# ---------------------------------------------------------
# Default Model Registrations (Regression)
# ---------------------------------------------------------
ModelCatalog.register(
    ModelMetadata(
        model_id="linear_regression",
        name="Linear Regression",
        supported_tasks=[TaskType.REGRESSION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_feature_importance=True,
        interpretability_score=9,
        estimated_training_speed=10,
        estimated_prediction_speed=10,
        module_path="sklearn.linear_model",
        class_name="LinearRegression",
        default_parameters={},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="ridge_regression",
        name="Ridge Regression",
        supported_tasks=[TaskType.REGRESSION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_feature_importance=True,
        interpretability_score=9,
        estimated_training_speed=10,
        estimated_prediction_speed=10,
        module_path="sklearn.linear_model",
        class_name="Ridge",
        default_parameters={"random_state": 42},
        hpo_param_space={"alpha": [0.1, 1.0, 10.0]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="lasso_regression",
        name="Lasso Regression",
        supported_tasks=[TaskType.REGRESSION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_feature_importance=True,
        interpretability_score=9,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="sklearn.linear_model",
        class_name="Lasso",
        default_parameters={"random_state": 42},
        hpo_param_space={"alpha": [0.01, 0.1, 1.0]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="elasticnet_regression",
        name="ElasticNet Regression",
        supported_tasks=[TaskType.REGRESSION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_feature_importance=True,
        interpretability_score=9,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="sklearn.linear_model",
        class_name="ElasticNet",
        default_parameters={"random_state": 42},
        hpo_param_space={"alpha": [0.1, 1.0], "l1_ratio": [0.2, 0.5, 0.8]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="random_forest_regressor",
        name="Random Forest Regressor",
        supported_tasks=[TaskType.REGRESSION, TaskType.FORECASTING],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=7,
        estimated_training_speed=6,
        estimated_prediction_speed=8,
        module_path="sklearn.ensemble",
        class_name="RandomForestRegressor",
        default_parameters={"n_estimators": 100, "random_state": 42},
        hpo_param_space={"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="xgboost_regressor",
        name="XGBoost Regressor",
        supported_tasks=[TaskType.REGRESSION, TaskType.FORECASTING],
        handles_missing_values=True,
        handles_categorical=True,
        supports_sparse=True,
        supports_gpu=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=8,
        estimated_prediction_speed=9,
        module_path="xgboost",
        class_name="XGBRegressor",
        default_parameters={"n_estimators": 100, "random_state": 42},
        hpo_param_space={
            "n_estimators": [50, 100],
            "learning_rate": [0.01, 0.1],
            "max_depth": [3, 6],
        },
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="lightgbm_regressor",
        name="LightGBM Regressor",
        supported_tasks=[TaskType.REGRESSION, TaskType.FORECASTING],
        handles_missing_values=True,
        handles_categorical=True,
        supports_sparse=True,
        supports_gpu=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="lightgbm",
        class_name="LGBMRegressor",
        default_parameters={"n_estimators": 100, "random_state": 42, "verbose": -1},
        hpo_param_space={"n_estimators": [50, 100], "learning_rate": [0.01, 0.1]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="catboost_regressor",
        name="CatBoost Regressor",
        supported_tasks=[TaskType.REGRESSION, TaskType.FORECASTING],
        handles_missing_values=True,
        handles_categorical=True,
        supports_gpu=True,
        supports_feature_importance=True,
        supports_shap=True,
        interpretability_score=6,
        estimated_training_speed=7,
        estimated_prediction_speed=9,
        module_path="catboost",
        class_name="CatBoostRegressor",
        default_parameters={"iterations": 100, "random_seed": 42, "verbose": 0},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="svr",
        name="Support Vector Regressor",
        supported_tasks=[TaskType.REGRESSION],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        interpretability_score=4,
        estimated_training_speed=4,
        estimated_prediction_speed=6,
        module_path="sklearn.svm",
        class_name="SVR",
        default_parameters={},
        hpo_param_space={"C": [0.1, 1.0, 10.0], "kernel": ["rbf", "linear"]},
    )
)

# ---------------------------------------------------------
# Default Model Registrations (Clustering)
# ---------------------------------------------------------
ModelCatalog.register(
    ModelMetadata(
        model_id="kmeans",
        name="K-Means Clustering",
        supported_tasks=[TaskType.CLUSTERING],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        interpretability_score=7,
        estimated_training_speed=9,
        estimated_prediction_speed=10,
        module_path="sklearn.cluster",
        class_name="KMeans",
        default_parameters={"n_clusters": 5, "random_state": 42},
        hpo_param_space={"n_clusters": [3, 5, 8, 10]},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="dbscan",
        name="DBSCAN Clustering",
        supported_tasks=[TaskType.CLUSTERING],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        interpretability_score=6,
        estimated_training_speed=7,
        estimated_prediction_speed=8,
        module_path="sklearn.cluster",
        class_name="DBSCAN",
        default_parameters={"eps": 0.5, "min_samples": 5},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="agglomerative",
        name="Agglomerative Clustering",
        supported_tasks=[TaskType.CLUSTERING],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=True,
        interpretability_score=6,
        estimated_training_speed=6,
        estimated_prediction_speed=6,
        module_path="sklearn.cluster",
        class_name="AgglomerativeClustering",
        default_parameters={"n_clusters": 5},
    )
)

ModelCatalog.register(
    ModelMetadata(
        model_id="gaussian_mixture",
        name="Gaussian Mixture Model",
        supported_tasks=[TaskType.CLUSTERING],
        handles_missing_values=False,
        handles_categorical=False,
        supports_sparse=False,
        interpretability_score=6,
        estimated_training_speed=7,
        estimated_prediction_speed=8,
        module_path="sklearn.mixture",
        class_name="GaussianMixture",
        default_parameters={"n_components": 5, "random_state": 42},
    )
)
