"""
CLI Experiments command for ML-OS.

Supports listing, showing, and comparing logged experiment runs.

Author: Antigravity
License: MIT
"""

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine
from mlos.experiment.comparator import ExperimentComparator
from mlos.experiment.tracker import ExperimentTracker


class ExperimentsCommand(BaseCommand):
    """
    Command to view and compare logged experiments.
    """

    @property
    def name(self) -> str:
        return "experiments"

    @property
    def help(self) -> str:
        return "List, inspect, and compare experiment runs."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos experiments\n"
            "  mlos experiments --show <exp_id>\n"
            "  mlos experiments --compare <exp_id1> <exp_id2>\n"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--show", type=str, help="Show details for an experiment ID"
        )
        parser.add_argument(
            "--compare",
            nargs=2,
            metavar=("EXP1", "EXP2"),
            help="Compare two experiment IDs",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()
        tracker = ExperimentTracker(project_root or ".")

        if args.show:
            exp = tracker.get_experiment(args.show)
            if not exp:
                console.print(
                    f"[bold red]Experiment '{args.show}' not found.[/bold red]"
                )
                return 1
            console.print(
                Panel(
                    f"[bold green]Experiment {exp['experiment_id']}[/bold green]",
                    expand=False,
                )
            )
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property")
            table.add_column("Value")
            for k, v in exp.items():
                table.add_row(k, str(v))
            console.print(table)
            return 0

        if args.compare:
            comparator = ExperimentComparator(tracker)
            try:
                diff = comparator.compare_experiments(args.compare[0], args.compare[1])
                console.print(
                    Panel(
                        f"[bold green]Experiment Comparison: {args.compare[0]} vs {args.compare[1]}[/bold green]"
                    )
                )
                table = Table(show_header=True, header_style="bold blue")
                table.add_column("Metric / Property")
                table.add_column(args.compare[0])
                table.add_column(args.compare[1])
                table.add_column("Difference")
                for k, v in diff.get("metric_comparison", {}).items():
                    table.add_row(k, str(v["exp1"]), str(v["exp2"]), str(v["diff"]))
                console.print(table)
                return 0
            except ValueError as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
                return 1

        exps = tracker.list_experiments()
        if not exps:
            console.print("[yellow]No experiments recorded yet.[/yellow]")
            return 0

        table = Table(
            title="ML-OS Experiment Runs", show_header=True, header_style="bold cyan"
        )
        table.add_column("ID", style="bold")
        table.add_column("Timestamp")
        table.add_column("Selected Model")
        table.add_column("Problem Type")
        table.add_column("CV Metric")

        for exp_rec in exps:
            metrics_str = ", ".join(
                f"{k}={v:.4f}" for k, v in exp_rec.get("metrics", {}).items()
            )
            table.add_row(
                exp_rec.get("experiment_id", ""),
                exp_rec.get("timestamp", "")[:19],
                exp_rec.get("selected_model", ""),
                exp_rec.get("problem_type", ""),
                metrics_str,
            )

        console.print(table)
        return 0
