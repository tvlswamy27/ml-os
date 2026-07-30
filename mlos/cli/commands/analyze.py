"""
CLI Analyze command.

Author: Vikram Tanakala
License: MIT
"""
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    update_project_config_from_memory,
)


class AnalyzeCommand(BaseCommand):
    """
    Command to run analysis on a dataset.
    """

    @property
    def name(self) -> str:
        return "analyze"

    @property
    def help(self) -> str:
        return "Analyze a dataset and profile its structure."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dataset", type=str, help="Path to the dataset file (CSV/Parquet)"
        )
        parser.add_argument("--target", type=str, help="Target column name")

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()

        if not project_root:
            console.print(
                "[bold red]Error: No active ML-OS project found. Run 'mlos init' first.[/bold red]"
            )
            return 1

        # Reconstruct ProjectMemory from config
        memory = reconstruct_project_memory(project_root)
        if not memory:
            console.print(
                "[bold red]Error: Failed to load project configuration from .mlos/project_config.yaml[/bold red]"
            )
            return 1

        # Determine dataset path and target
        dataset_path = args.dataset
        if not dataset_path:
            if memory.dataset and memory.dataset.path:
                dataset_path = memory.dataset.path
            else:
                console.print(
                    "[bold red]Error: Please specify a dataset path via --dataset.[/bold red]"
                )
                return 1

        target = args.target or (memory.dataset.target if memory.dataset else None)

        engine.project_memory = memory

        with console.status("[bold green]Running dataset analysis...[/bold green]"):
            try:
                report = engine.run_analysis(dataset_path, target)
                # Synchronize memory back to config
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(
                    f"[bold red]Failed to execute analysis: {e}[/bold red]"
                )
                return 1

        # Print Analysis Report using Rich
        console.print(
            Panel(
                f"[bold green]Analysis Complete for Project: {memory.project_name}[/bold green]",
                expand=False,
            )
        )

        # Dataset Metadata Table
        dataset = report.dataset
        meta_table = Table(title="Dataset Summary", show_header=True, header_style="bold magenta")
        meta_table.add_column("Property", style="dim")
        meta_table.add_column("Value")
        meta_table.add_row("Path", str(dataset.path))
        meta_table.add_row("Rows", str(dataset.rows))
        meta_table.add_row("Columns", str(dataset.columns))
        meta_table.add_row("Target Feature", str(dataset.target or "None"))
        meta_table.add_row("Problem Type", str(dataset.problem_type or "Unknown"))
        meta_table.add_row("Duplicate Rows", str(dataset.duplicate_rows))
        console.print(meta_table)

        # Columns Summary
        console.print(f"[bold cyan]Numerical Columns ({len(dataset.numerical_columns)}):[/bold cyan] {', '.join(dataset.numerical_columns[:10])}" + ("..." if len(dataset.numerical_columns) > 10 else ""))
        console.print(f"[bold cyan]Categorical Columns ({len(dataset.categorical_columns)}):[/bold cyan] {', '.join(dataset.categorical_columns[:10])}" + ("..." if len(dataset.categorical_columns) > 10 else ""))

        # Decisions Table
        if report.decisions:
            dec_table = Table(title="Decisions Formulated", show_header=True, header_style="bold yellow")
            dec_table.add_column("Title", style="bold")
            dec_table.add_column("Strategy")
            dec_table.add_column("Confidence")
            dec_table.add_column("Reason")
            for dec in report.decisions:
                dec_table.add_row(dec.title, dec.strategy, dec.confidence, dec.reason)
            console.print(dec_table)
        else:
            console.print("[yellow]No preprocessing/modeling decisions formulated.[/yellow]")

        # Recommendations Table
        if report.recommendations:
            rec_table = Table(title="Recommendations", show_header=True, header_style="bold blue")
            rec_table.add_column("Priority", style="bold")
            rec_table.add_column("Title", style="bold")
            rec_table.add_column("Description")
            for rec in report.recommendations:
                priority_color = "red" if rec.priority.value == "HIGH" else ("yellow" if rec.priority.value == "MEDIUM" else "green")
                rec_table.add_row(
                    f"[{priority_color}]{rec.priority.value}[/{priority_color}]",
                    rec.title,
                    rec.description,
                )
            console.print(rec_table)

        return 0
