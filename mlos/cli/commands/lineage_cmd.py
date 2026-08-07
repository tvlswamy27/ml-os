"""
CLI Lineage command for ML-OS.

View end-to-end lineage tracking records.

Author: Antigravity
License: MIT
"""

import argparse
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine


class LineageCommand(BaseCommand):
    """
    Command to inspect lineage records.
    """

    @property
    def name(self) -> str:
        return "lineage"

    @property
    def help(self) -> str:
        return "Inspect end-to-end dataset-to-model lineage."

    @property
    def epilog(self) -> str:
        return "Examples:\n  mlos lineage\n"

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()
        lineage_file = (
            (project_root or Path(".")).resolve()
            / "artifacts"
            / "automl"
            / "lineage.json"
        )

        if not lineage_file.exists():
            console.print(
                "[yellow]No lineage record found in artifacts/automl/lineage.json. Run 'mlos run' or AutoML first.[/yellow]"
            )
            return 0

        try:
            data = json.loads(lineage_file.read_text(encoding="utf-8"))
            console.print(
                Panel("[bold green]ML-OS End-to-End Lineage[/bold green]", expand=False)
            )
            console.print(
                f"[bold cyan]Dataset Fingerprint:[/bold cyan] {data.get('dataset_fingerprint')}"
            )
            console.print(
                f"[bold cyan]Features ({len(data.get('feature_columns', []))}):[/bold cyan] {', '.join(data.get('feature_columns', [])[:5])}..."
            )
            console.print(
                f"[bold cyan]Pipeline ID:[/bold cyan] {data.get('pipeline_id')}"
            )
            console.print(f"[bold cyan]Model ID:[/bold cyan] {data.get('model_id')}")
            console.print(
                f"[bold cyan]Experiment ID:[/bold cyan] {data.get('experiment_id')}"
            )
            console.print(
                f"[bold cyan]Deployment Stage:[/bold cyan] {data.get('deployment_stage')}"
            )
            return 0
        except Exception as e:
            console.print(f"[bold red]Error reading lineage file: {e}[/bold red]")
            return 1
