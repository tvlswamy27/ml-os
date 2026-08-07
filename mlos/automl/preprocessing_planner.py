"""
Preprocessing Planner for ML-OS AutoML Engine.

Generates tailored scikit-learn Pipeline preprocessors specific to model family requirements.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

from mlos.domain.models.dataset import Dataset
from mlos.models.catalog import ModelMetadata


@dataclass
class PreprocessingPlan:
    """Plan details for preprocessing a dataset for a specific model."""

    model_id: str
    scaling_required: bool = False
    encoding_strategy: str = "onehot"  # "onehot", "ordinal", "passthrough"
    imputation_strategy: str = "median"
    sparse_matrix_output: bool = False
    numerical_features: list[str] = field(default_factory=list)
    categorical_features: list[str] = field(default_factory=list)
    transformer: ColumnTransformer | None = None


class PreprocessingPlanner:
    """
    Creates custom Scikit-Learn transformers customized for candidate models.
    """

    def plan_and_build(
        self, dataset: Dataset, model_meta: ModelMetadata
    ) -> PreprocessingPlan:
        """
        Build an optimal ColumnTransformer preprocessor for the given model metadata.
        """
        num_cols = [c for c in dataset.numerical_columns if c != dataset.target]
        cat_cols = [
            c
            for c in dataset.categorical_columns
            if c != dataset.target
            and c not in dataset.id_columns
            and c not in dataset.text_columns
        ]

        is_tree = any(
            k in model_meta.model_id
            for k in ["forest", "tree", "boost", "xgb", "lgbm", "catboost"]
        )
        is_linear = any(
            k in model_meta.model_id
            for k in [
                "linear",
                "logistic",
                "ridge",
                "lasso",
                "elastic",
                "svc",
                "svr",
                "knn",
            ]
        )

        scaling_required = is_linear
        encoding_strategy = "onehot" if (is_linear or len(cat_cols) <= 5) else "ordinal"

        if model_meta.handles_categorical:
            encoding_strategy = "ordinal"

        transformers = []

        # Numerical pipeline
        if num_cols:
            num_steps = [("imputer", SimpleImputer(strategy="median"))]
            if scaling_required:
                num_steps.append(("scaler", StandardScaler()))
            num_pipe = Pipeline(num_steps)
            transformers.append(("num", num_pipe, num_cols))

        # Categorical pipeline
        if cat_cols:
            if encoding_strategy == "onehot":
                cat_pipe = Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                )
            else:
                cat_pipe = Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "ordinal",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value", unknown_value=-1
                            ),
                        ),
                    ]
                )
            transformers.append(("cat", cat_pipe, cat_cols))

        transformer = (
            ColumnTransformer(transformers=transformers, remainder="drop")
            if transformers
            else None
        )

        return PreprocessingPlan(
            model_id=model_meta.model_id,
            scaling_required=scaling_required,
            encoding_strategy=encoding_strategy,
            imputation_strategy="median",
            sparse_matrix_output=model_meta.supports_sparse and is_linear,
            numerical_features=num_cols,
            categorical_features=cat_cols,
            transformer=transformer,
        )
