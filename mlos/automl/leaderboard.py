"""
Multi-Objective Leaderboard Generator and Selection Audit for ML-OS.

Author: Antigravity
License: MIT
"""

import csv
import json
from pathlib import Path
from typing import Any

from mlos.domain.models.model_result import ModelResult
from mlos.models.model_recommender import ModelRecommendation


class LeaderboardGenerator:
    """
    Ranks evaluated models across accuracy, speed, memory, and explainability.
    Generates leaderboard.csv, leaderboard.json, leaderboard.md, and model_selection_audit.md.
    """

    def generate(
        self,
        output_dir: Path,
        results: list[ModelResult],
        recommendations: list[ModelRecommendation],
        dataset_info: dict[str, Any],
    ) -> dict[str, str]:
        """
        Generate leaderboard artifacts and audit log.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        successful_results = [r for r in results if r.status == "SUCCESS"]
        successful_results.sort(key=lambda r: r.cv_mean, reverse=True)

        # Categorical winners
        best_accuracy = successful_results[0] if successful_results else None
        fastest_model = (
            min(successful_results, key=lambda r: r.training_time)
            if successful_results
            else None
        )
        most_explainable = (
            max(
                successful_results,
                key=lambda r: r.model_id
                in [
                    "logistic_regression",
                    "decision_tree_classifier",
                    "random_forest_classifier",
                ],
            )
            if successful_results
            else None
        )

        # 1. JSON
        json_data = {
            "dataset": dataset_info,
            "best_accuracy": best_accuracy.model_name if best_accuracy else None,
            "fastest_model": fastest_model.model_name if fastest_model else None,
            "leaderboard": [
                {
                    "rank": idx + 1,
                    "model_id": r.model_id,
                    "model_name": r.model_name,
                    "status": r.status,
                    "cv_mean": round(r.cv_mean, 4),
                    "cv_std": round(r.cv_std, 4),
                    "training_time": round(r.training_time, 3),
                    "prediction_time": round(r.prediction_time, 4),
                    "memory_usage_mb": round(r.memory_usage_mb, 2),
                    "model_size_bytes": r.model_size_bytes,
                }
                for idx, r in enumerate(successful_results)
            ],
        }
        json_path = output_dir / "leaderboard.json"
        json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

        # 2. CSV
        csv_path = output_dir / "leaderboard.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "rank",
                    "model_id",
                    "model_name",
                    "status",
                    "cv_mean",
                    "cv_std",
                    "training_time_s",
                    "prediction_time_s",
                    "memory_mb",
                    "model_size_bytes",
                ]
            )
            for idx, r in enumerate(successful_results, start=1):
                writer.writerow(
                    [
                        idx,
                        r.model_id,
                        r.model_name,
                        r.status,
                        round(r.cv_mean, 4),
                        round(r.cv_std, 4),
                        round(r.training_time, 3),
                        round(r.prediction_time, 4),
                        round(r.memory_usage_mb, 2),
                        r.model_size_bytes,
                    ]
                )

        # 3. Leaderboard Markdown
        md_lines = [
            "# ML-OS AutoML Model Leaderboard",
            f"**Dataset**: `{dataset_info.get('path', 'Dataset')}` | **Problem Type**: `{dataset_info.get('problem_type', 'N/A')}` | **Total Samples**: {dataset_info.get('rows', 0)}\n",
            "| Rank | Model Name | Status | CV Mean | CV Std | Train Time (s) | Predict Time (s) | Memory (MB) |",
            "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for idx, r in enumerate(successful_results, start=1):
            md_lines.append(
                f"| {idx} | **{r.model_name}** | `{r.status}` | {r.cv_mean:.4f} | ±{r.cv_std:.4f} | {r.training_time:.3f}s | {r.prediction_time:.4f}s | {r.memory_usage_mb:.2f} MB |"
            )

        md_path = output_dir / "leaderboard.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        # 4. Selection Audit Markdown
        audit_lines = [
            "# Model Selection Audit Report",
            "## 1. Dataset Characteristics",
            f"- **Rows**: {dataset_info.get('rows', 0)}",
            f"- **Columns**: {dataset_info.get('columns', 0)}",
            f"- **Problem Type**: {dataset_info.get('problem_type', 'N/A')}",
            f"- **Class Imbalance Ratio**: {dataset_info.get('imbalance_ratio', 'None')}\n",
            "## 2. Candidate Model Evaluation & Rejections",
            "| Model | Initial Rank | Availability | Status / Rejection Reason |",
            "| :--- | :---: | :---: | :--- |",
        ]
        for rec in recommendations:
            avail_str = "Available" if rec.is_available else "Not Installed"
            reason_str = rec.rejection_reason or (
                rec.reasoning[0] if rec.reasoning else "Selected"
            )
            audit_lines.append(
                f"| {rec.name} | {rec.rank} | {avail_str} | {reason_str} |"
            )

        best_acc_str = (
            f"{best_accuracy.cv_mean:.4f}" if best_accuracy else "N/A"
        )
        fastest_str = (
            f"{fastest_model.prediction_time:.4f}s"
            if fastest_model
            else "N/A"
        )
        audit_lines.extend(
            [
                "\n## 3. Winner Selection Rationale",
                f"- **Best Overall Accuracy Candidate**: `{best_accuracy.model_name if best_accuracy else 'None'}` (CV Score: {best_acc_str})",
                f"- **Fastest Inference Candidate**: `{fastest_model.model_name if fastest_model else 'None'}` ({fastest_str} latency)",
            ]
        )

        audit_path = output_dir / "model_selection_audit.md"
        audit_path.write_text("\n".join(audit_lines), encoding="utf-8")

        return {
            "leaderboard_json": str(json_path),
            "leaderboard_csv": str(csv_path),
            "leaderboard_md": str(md_path),
            "audit_md": str(audit_path),
        }
