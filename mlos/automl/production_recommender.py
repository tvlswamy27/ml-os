"""
Production Deployment Recommendation Engine for ML-OS.

Generates deployment recommendations and rationale in automl_summary.md / json.

Author: Antigravity
License: MIT
"""

import json
from pathlib import Path
from typing import Any

from mlos.domain.models.model_result import ModelResult


class ProductionRecommender:
    """
    Generates categorical production recommendations (Best Accuracy, Speed, Explainability, Overall).
    """

    def generate_recommendation(
        self,
        output_dir: Path,
        results: list[ModelResult],
        dataset_info: dict[str, Any],
    ) -> dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        successful = [r for r in results if r.status == "SUCCESS"]

        if not successful:
            summary_data = {"error": "No model was successfully trained."}
            json_path = output_dir / "automl_summary.json"
            json_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
            return {"summary_json": str(json_path)}

        successful.sort(key=lambda r: r.cv_mean, reverse=True)
        best_acc = successful[0]
        fastest = min(successful, key=lambda r: r.prediction_time)

        # Most explainable
        explainable = next(
            (
                r
                for r in successful
                if r.model_id
                in [
                    "logistic_regression",
                    "linear_regression",
                    "decision_tree_classifier",
                ]
            ),
            best_acc,
        )

        # Best overall Pareto candidate (combining CV score and prediction speed)
        best_overall = best_acc
        for r in successful:
            if (
                r.cv_mean >= best_acc.cv_mean * 0.98
                and r.prediction_time < best_acc.prediction_time * 0.5
            ):
                best_overall = r
                break

        summary_dict = {
            "dataset": dataset_info,
            "best_accuracy": {
                "model_id": best_acc.model_id,
                "model_name": best_acc.model_name,
                "cv_score": round(best_acc.cv_mean, 4),
            },
            "best_speed": {
                "model_id": fastest.model_id,
                "model_name": fastest.model_name,
                "prediction_time_s": round(fastest.prediction_time, 4),
            },
            "best_explainability": {
                "model_id": explainable.model_id,
                "model_name": explainable.model_name,
                "method": explainable.explainability_method,
            },
            "best_overall_production_candidate": {
                "model_id": best_overall.model_id,
                "model_name": best_overall.model_name,
                "cv_score": round(best_overall.cv_mean, 4),
                "prediction_time_s": round(best_overall.prediction_time, 4),
                "rationale": f"Selected for optimal balance of CV performance ({best_overall.cv_mean:.4f}) and low inference latency ({best_overall.prediction_time:.4f}s).",
            },
        }

        json_path = output_dir / "automl_summary.json"
        json_path.write_text(json.dumps(summary_dict, indent=2), encoding="utf-8")

        md_lines = [
            "# ML-OS Production Deployment Recommendation",
            "## Summary Categorical Winners\n",
            f"- **Best Accuracy**: `{best_acc.model_name}` (CV Score: `{best_acc.cv_mean:.4f}`)",
            f"- **Best Speed**: `{fastest.model_name}` (Prediction Latency: `{fastest.prediction_time:.4f}s`)",
            f"- **Best Explainability**: `{explainable.model_name}` (Method: `{explainable.explainability_method}`)",
            f"- **Best Overall Production Candidate**: `{best_overall.model_name}`\n",
            "## Production Recommendation Rationale",
            f"{summary_dict['best_overall_production_candidate']['rationale']}\n",
            "## Recommended Deployment Pipeline Steps",
            "1. Load preprocessor and model from `artifacts/models/`",
            "2. Apply standard feature transformations",
            "3. Serve inference via standard python executable or API service",
        ]

        md_path = output_dir / "automl_summary.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        return {
            "summary_json": str(json_path),
            "summary_md": str(md_path),
        }
