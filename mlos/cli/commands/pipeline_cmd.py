"""
CLI Pipeline command for ML-OS.

Supports listing, exporting, and inspecting reusable ML pipelines.

Author: Antigravity
License: MIT
"""

import argparse

from rich.console import Console
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine
from mlos.pipeline.registry import PipelineRegistry


class PipelineCommand(BaseCommand):
    """
    Command to list and export reusable ML pipelines.
    """

    @property
    def name(self) -> str:
        return "pipeline"

    @property
    def help(self) -> str:
        return "List and export reusable ML pipelines."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos pipeline --list\n"
            "  mlos pipeline --export <pipeline_id> --out pipeline_export.zip\n"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--list", action="store_true", help="List registered pipelines"
        )
        parser.add_argument("--export", type=str, help="Pipeline ID to export")
        parser.add_argument(
            "--out", type=str, default="pipeline.zip", help="Output export path"
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()
        reg = PipelineRegistry(project_root or ".")

        if args.export:
            try:
                arc = reg.export_pipeline(args.export, args.out)
                console.print(
                    f"[bold green]Pipeline '{args.export}' exported to {arc}[/bold green]"
                )
                return 0
            except Exception as e:
                console.print(f"[bold red]Failed to export pipeline: {e}[/bold red]")
                return 1

        pipelines = reg.list_pipelines()
        if not pipelines:
            console.print("[yellow]No registered pipelines found.[/yellow]")
            return 0

        table = Table(
            title="ML-OS Registered Pipelines",
            show_header=True,
            header_style="bold green",
        )
        table.add_column("Pipeline ID", style="bold")
        table.add_column("Model ID")
        table.add_column("Version")
        table.add_column("Created At")

        for p in pipelines:
            table.add_row(
                p.get("pipeline_id", ""),
                p.get("model_id", ""),
                p.get("version", ""),
                p.get("created_at", "")[:19],
            )

        console.print(table)
        return 0
