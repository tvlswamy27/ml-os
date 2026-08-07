"""
End-to-End Lineage Tracking Engine for ML-OS.

Generates lineage.json and lineage.md mapping Dataset -> Features -> Pipeline -> Model -> Experiment -> Artifacts -> Deployment.

Author: Antigravity
License: MIT
"""

import json
from pathlib import Path


class LineageTracker:
    """
    Generates lineage tracking records and documentation artifacts.
    """

    def generate_lineage(
        self,
        output_dir: Path | str,
        dataset_fingerprint: str,
        features: list[str],
        pipeline_id: str,
        model_id: str,
        experiment_id: str,
        artifacts: dict[str, str],
        deployment_stage: str = "staging",
    ) -> dict[str, str]:
        """
        Generate lineage.json and lineage.md.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        lineage_dict = {
            "dataset_fingerprint": dataset_fingerprint,
            "feature_columns": features,
            "pipeline_id": pipeline_id,
            "model_id": model_id,
            "experiment_id": experiment_id,
            "artifacts": artifacts,
            "deployment_stage": deployment_stage,
        }

        json_path = out_path / "lineage.json"
        json_path.write_text(json.dumps(lineage_dict, indent=2), encoding="utf-8")

        md_lines = [
            "# ML-OS End-to-End Lineage Report",
            "```mermaid",
            "graph TD;",
            f"  Dataset['Dataset ({dataset_fingerprint[:8]})'] --> Features['Features ({len(features)} cols)'];",
            f"  Features --> Pipeline['Pipeline ({pipeline_id})'];",
            f"  Pipeline --> Model['Model ({model_id})'];",
            f"  Model --> Experiment['Experiment ({experiment_id})'];",
            f"  Experiment --> Deployment['Deployment ({deployment_stage})'];",
            "```\n",
            "## Artifact Lineage Details",
            f"- **Dataset Fingerprint**: `{dataset_fingerprint}`",
            f"- **Pipeline ID**: `{pipeline_id}`",
            f"- **Model ID**: `{model_id}`",
            f"- **Experiment ID**: `{experiment_id}`",
            f"- **Deployment Stage**: `{deployment_stage}`\n",
            "## Key Generated Artifacts",
        ]
        for name, p in artifacts.items():
            md_lines.append(f"- **{name}**: `{p}`")

        md_path = out_path / "lineage.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        return {
            "lineage_json": str(json_path),
            "lineage_md": str(md_path),
        }
