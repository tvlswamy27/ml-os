"""
Experiment Comparison Engine for ML-OS.

Compares metrics, runtime, memory, parameters, and pipeline differences between experiment runs.

Author: Antigravity
License: MIT
"""

from typing import Any

from mlos.experiment.tracker import ExperimentTracker


class ExperimentComparator:
    """
    Compares two or more experiment runs side-by-side.
    """

    def __init__(self, tracker: ExperimentTracker):
        self.tracker = tracker

    def compare_experiments(self, exp_id1: str, exp_id2: str) -> dict[str, Any]:
        """
        Compare two experiment runs.
        """
        e1 = self.tracker.get_experiment(exp_id1)
        e2 = self.tracker.get_experiment(exp_id2)

        if not e1 or not e2:
            raise ValueError("One or both experiment IDs not found in tracker.")

        metric_diffs = {}
        all_metrics = set(e1.get("metrics", {}).keys()) | set(
            e2.get("metrics", {}).keys()
        )
        for k in all_metrics:
            v1 = e1.get("metrics", {}).get(k, 0.0)
            v2 = e2.get("metrics", {}).get(k, 0.0)
            metric_diffs[k] = {
                "exp1": v1,
                "exp2": v2,
                "diff": round(v2 - v1, 4),
            }

        return {
            "exp1_id": exp_id1,
            "exp2_id": exp_id2,
            "models": {
                "exp1": e1.get("selected_model"),
                "exp2": e2.get("selected_model"),
            },
            "metric_comparison": metric_diffs,
            "training_time": {
                "exp1": e1.get("training_time_s"),
                "exp2": e2.get("training_time_s"),
                "diff_s": round(
                    e2.get("training_time_s", 0) - e1.get("training_time_s", 0), 3
                ),
            },
            "prediction_time": {
                "exp1": e1.get("prediction_time_s"),
                "exp2": e2.get("prediction_time_s"),
                "diff_s": round(
                    e2.get("prediction_time_s", 0) - e1.get("prediction_time_s", 0), 4
                ),
            },
            "memory_mb": {
                "exp1": e1.get("memory_usage_mb"),
                "exp2": e2.get("memory_usage_mb"),
            },
        }
