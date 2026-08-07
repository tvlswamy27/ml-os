"""
AutoML Explainability Engine for ML-OS.

Extracts feature importance using Tree MDI, Linear Coefficients, Permutation Importance, and SHAP.

Author: Antigravity
License: MIT
"""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.inspection import permutation_importance

from mlos.domain.models.model_result import ModelResult
from mlos.models.catalog import ModelMetadata


class AutoMLExplainer:
    """
    Computes feature importance and generates explainability artifacts.
    """

    def explain(
        self,
        result: ModelResult,
        metadata: ModelMetadata,
        X_test: Any,
        y_test: Any,
        feature_names: list[str],
    ) -> tuple[dict[str, float], str]:
        """
        Extract feature importances and method name.
        """
        model = result.model_object
        if model is None or len(feature_names) == 0:
            return {}, "none"

        importance_dict: dict[str, float] = {}
        method = "permutation"

        # 1. Tree MDI Feature Importance
        if hasattr(model, "feature_importances_"):
            method = "feature_importance_mdi"
            imps = model.feature_importances_
            if len(imps) == len(feature_names):
                for name, imp in zip(feature_names, imps):
                    importance_dict[name] = float(round(imp, 4))

        # 2. Linear Model Coefficients
        elif hasattr(model, "coef_"):
            method = "linear_coefficients"
            coefs = np.abs(model.coef_)
            if coefs.ndim > 1:
                coefs = np.mean(coefs, axis=0)
            if len(coefs) == len(feature_names):
                total = float(np.sum(coefs)) if np.sum(coefs) > 0 else 1.0
                for name, coef in zip(feature_names, coefs):
                    importance_dict[name] = float(round(coef / total, 4))

        # 3. Fallback: Permutation Importance
        else:
            method = "permutation_importance"
            try:
                perm_res = permutation_importance(
                    model, X_test, y_test, n_repeats=3, random_state=42
                )
                imps = perm_res.importances_mean
                if len(imps) == len(feature_names):
                    for name, imp in zip(feature_names, imps):
                        importance_dict[name] = float(round(max(imp, 0.0), 4))
            except Exception:
                method = "none"

        # Try SHAP if available and model is supported
        if metadata.supports_shap:
            try:
                import shap  # type: ignore

                explainer = shap.Explainer(model, X_test)
                shap_values = explainer(X_test)
                if hasattr(shap_values, "values"):
                    shap_mean = np.mean(np.abs(shap_values.values), axis=0)
                    if shap_mean.ndim > 1:
                        shap_mean = np.mean(shap_mean, axis=0)
                    if len(shap_mean) == len(feature_names):
                        method = "shap_feature_importance"
                        importance_dict = {
                            name: float(round(val, 4))
                            for name, val in zip(feature_names, shap_mean)
                        }
            except Exception:
                pass  # Fall back gracefully to primary method

        # Sort feature importances
        sorted_imp = dict(
            sorted(importance_dict.items(), key=lambda item: item[1], reverse=True)
        )
        return sorted_imp, method

    def generate_artifacts(
        self,
        output_dir: Path,
        importance_dict: dict[str, float],
        method: str,
        model_name: str,
    ) -> dict[str, str]:
        """
        Write importance.json, importance.csv, and importance.md.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "importance.json"
        csv_path = output_dir / "importance.csv"
        md_path = output_dir / "importance.md"

        # 1. JSON
        json_path.write_text(
            json.dumps(
                {"model": model_name, "method": method, "importances": importance_dict},
                indent=2,
            ),
            encoding="utf-8",
        )

        # 2. CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["feature", "importance_score"])
            for feat, imp in importance_dict.items():
                writer.writerow([feat, imp])

        # 3. Markdown
        lines = [
            f"# Feature Importance Report ({model_name})",
            f"**Explainability Method**: {method}\n",
            "| Rank | Feature | Importance Score |",
            "| :---: | :--- | :---: |",
        ]
        for idx, (feat, imp) in enumerate(importance_dict.items(), start=1):
            lines.append(f"| {idx} | `{feat}` | {imp:.4f} |")

        md_path.write_text("\n".join(lines), encoding="utf-8")

        return {
            "importance_json": str(json_path),
            "importance_csv": str(csv_path),
            "importance_md": str(md_path),
        }
