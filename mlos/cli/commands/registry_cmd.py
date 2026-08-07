"""
CLI Registry command for ML-OS.

Inspect and manage model versions and deployment stages.

Author: Antigravity
License: MIT
"""

import argparse

from rich.console import Console
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine
from mlos.registry.model_registry import ModelRegistry


class RegistryCommand(BaseCommand):
    """
    Command to inspect and manage the Versioned Model Registry.
    """

    @property
    def name(self) -> str:
        return "registry"

    @property
    def help(self) -> str:
        return "Inspect and manage model deployment registry."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos registry\n"
            "  mlos registry --transition <model_id> <version> --stage production\n"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--transition",
            nargs=2,
            metavar=("MODEL_ID", "VERSION"),
            help="Model ID and version to transition",
        )
        parser.add_argument(
            "--stage",
            type=str,
            choices=["staging", "production", "archived", "rollback"],
            default="production",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()
        reg = ModelRegistry(project_root or ".")

        if args.transition:
            ok = reg.transition_stage(
                args.transition[0], args.transition[1], args.stage
            )
            if ok:
                console.print(
                    f"[bold green]Successfully transitioned {args.transition[0]}:{args.transition[1]} to stage '{args.stage}'[/bold green]"
                )
                return 0
            else:
                console.print(
                    f"[bold red]Model version '{args.transition[0]}:{args.transition[1]}' not found.[/bold red]"
                )
                return 1

        models = reg.list_models()
        if not models:
            console.print("[yellow]No models registered in registry.[/yellow]")
            return 0

        table = Table(
            title="ML-OS Model Registry", show_header=True, header_style="bold blue"
        )
        table.add_column("Model ID", style="bold")
        table.add_column("Version")
        table.add_column("Stage")
        table.add_column("Approval Status")
        table.add_column("Metrics")

        for m in models:
            m_str = ", ".join(f"{k}={v:.4f}" for k, v in m.get("metrics", {}).items())
            table.add_row(
                m.get("model_id", ""),
                m.get("version", ""),
                m.get("stage", ""),
                m.get("approval_status", ""),
                m_str,
            )

        console.print(table)
        return 0
