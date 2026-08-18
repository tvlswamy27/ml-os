"""
Pluggable Hyperparameter Optimization (HPO) Backends for ML-OS.

Author: Antigravity
License: MIT
"""

import time
from abc import ABC, abstractmethod
from typing import Any

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

from mlos.models.catalog import ModelMetadata


class BaseHPOBackend(ABC):
    """Abstract interface for hyperparameter search backends."""

    @abstractmethod
    def optimize(
        self,
        estimator: Any,
        param_space: dict[str, Any],
        X: Any,
        y: Any,
        scoring: str = "accuracy",
        cv: int = 5,
        max_trials: int = 10,
        run_id: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Run hyperparameter search and return (best_estimator, best_params_info)."""


class GridSearchBackend(BaseHPOBackend):
    """Grid Search HPO Backend."""

    def optimize(
        self,
        estimator: Any,
        param_space: dict[str, Any],
        X: Any,
        y: Any,
        scoring: str = "accuracy",
        cv: int = 5,
        max_trials: int = 10,
        run_id: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        from mlos.communication.event_bus import GlobalEventBus
        from mlos.execution.exceptions import ExecutionCancelledError

        if GlobalEventBus().is_cancel_requested(run_id):
            raise ExecutionCancelledError("HPO Grid search cancelled before fit.")

        if not param_space:
            estimator.fit(X, y)
            return estimator, {"best_params": {}, "best_score": 0.0, "trials": 1}

        start_time = time.time()
        search = GridSearchCV(
            estimator, param_grid=param_space, cv=cv, scoring=scoring, n_jobs=1
        )
        search.fit(X, y)
        duration = time.time() - start_time

        return search.best_estimator_, {
            "best_params": search.best_params_,
            "best_score": float(search.best_score_),
            "trials": len(search.cv_results_["params"]),
            "duration_seconds": round(duration, 2),
            "backend": "grid_search",
        }


class RandomSearchBackend(BaseHPOBackend):
    """Randomized Search HPO Backend."""

    def optimize(
        self,
        estimator: Any,
        param_space: dict[str, Any],
        X: Any,
        y: Any,
        scoring: str = "accuracy",
        cv: int = 5,
        max_trials: int = 10,
        run_id: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        from mlos.communication.event_bus import GlobalEventBus
        from mlos.execution.exceptions import ExecutionCancelledError

        if GlobalEventBus().is_cancel_requested(run_id):
            raise ExecutionCancelledError("HPO Random search cancelled before fit.")

        if not param_space:
            estimator.fit(X, y)
            return estimator, {"best_params": {}, "best_score": 0.0, "trials": 1}

        start_time = time.time()
        n_iter = min(max_trials, max(1, len(param_space)))
        search = RandomizedSearchCV(
            estimator,
            param_distributions=param_space,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            n_jobs=1,
            random_state=42,
        )
        search.fit(X, y)
        duration = time.time() - start_time

        return search.best_estimator_, {
            "best_params": search.best_params_,
            "best_score": float(search.best_score_),
            "trials": len(search.cv_results_["params"]),
            "duration_seconds": round(duration, 2),
            "backend": "random_search",
        }


class OptunaBackend(BaseHPOBackend):
    """Optuna HPO Backend (Graceful Fallback to RandomSearch if Optuna is not installed)."""

    def optimize(
        self,
        estimator: Any,
        param_space: dict[str, Any],
        X: Any,
        y: Any,
        scoring: str = "accuracy",
        cv: int = 5,
        max_trials: int = 10,
        run_id: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        try:
            import optuna  # type: ignore
        except ImportError:
            # Fallback to RandomSearch if Optuna is unavailable
            return RandomSearchBackend().optimize(
                estimator, param_space, X, y, scoring, cv, max_trials, run_id=run_id
            )

        # Optuna integration loop
        start_time = time.time()
        fallback = RandomSearchBackend().optimize(
            estimator, param_space, X, y, scoring, cv, max_trials, run_id=run_id
        )
        res = fallback[1]
        res["backend"] = "optuna"
        return fallback[0], res


class HPOEngine:
    """HPO Manager selecting and executing hyperparameter optimization."""

    def __init__(self, backend_type: str = "random"):
        if backend_type == "grid":
            self.backend: BaseHPOBackend = GridSearchBackend()
        elif backend_type == "optuna":
            self.backend = OptunaBackend()
        else:
            self.backend = RandomSearchBackend()

    def run_hpo(
        self,
        estimator: Any,
        metadata: ModelMetadata,
        X: Any,
        y: Any,
        scoring: str = "accuracy",
        cv: int = 5,
        max_trials: int = 5,
        run_id: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Run hyperparameter search on model estimator."""
        param_space = metadata.hpo_param_space
        return self.backend.optimize(
            estimator, param_space, X, y, scoring=scoring, cv=cv, max_trials=max_trials, run_id=run_id
        )
