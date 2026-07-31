"""
CLI benchmark command.

Author: Antigravity
License: MIT
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.benchmark.framework import BenchmarkRunner


class BenchmarkCommand(BaseCommand):
    """
    Evaluates ML-OS cognitive subsystems performance, accuracy, costs, and robustness.
    """

    @property
    def name(self) -> str:
        return "benchmark"

    @property
    def help(self) -> str:
        return "Compare RULE vs LLM vs HYBRID modes on datasets and log metrics."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "datasets",
            nargs="*",
            help="Paths to dataset CSV files. If omitted, uses default playground/sample.csv.",
        )
        parser.add_argument(
            "--output-dir",
            default="benchmark",
            help="Directory to save benchmark report outputs (run.json, run.csv, summary.md).",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()

        datasets = args.datasets
        if not datasets:
            # Check for playground/sample.csv as fallback
            default_csv = Path("playground/sample.csv")
            if default_csv.exists():
                datasets = [str(default_csv)]
            else:
                console.print(
                    "[bold red]Error: No datasets specified and playground/sample.csv not found.[/bold red]"
                )
                return 1

        output_dir = Path(args.output_dir)

        console.print(
            Panel(
                f"[bold green]Starting ML-OS benchmark suite run...[/bold green]\n"
                f"[cyan]Datasets to evaluate:[/cyan] {datasets}\n"
                f"[cyan]Report destination folder:[/cyan] {output_dir.absolute()}",
                expand=False,
            )
        )

        runner = BenchmarkRunner(datasets)
        with console.status(
            "[bold green]Executing benchmark runs across cognitive modes...[/bold green]"
        ):
            try:
                results = runner.run_benchmark()
                runner.save_outputs(output_dir)
            except Exception as e:
                console.print(f"[bold red]Benchmark run failed: {e}[/bold red]")
                import traceback

                console.print(traceback.format_exc())
                return 1

        # Print results table
        table = Table(title="ML-OS Mode Comparison Results Summary", expand=False)
        table.add_column("Dataset", style="white")
        table.add_column("Mode", style="magenta")
        table.add_column("Latency (s)", style="green")
        table.add_column("Accuracy", style="cyan")
        table.add_column("F1 Score", style="cyan")
        table.add_column("Token Count", style="yellow")
        table.add_column("Est. Cost ($)", style="yellow")
        table.add_column("Cache Hit Rate", style="blue")
        table.add_column("Fallbacks", style="red")

        for r in results:
            table.add_row(
                r["dataset"],
                r["mode"],
                f"{r['latency_sec']:.3f} s",
                f"{r['accuracy']:.2f}",
                f"{r['f1']:.2f}",
                str(r["token_usage"]),
                f"${r['estimated_cost']:.5f}",
                f"{r['cache_hit_rate'] * 100:.1f}%",
                str(r["fallback_frequency"]),
            )

        console.print(table)
        console.print(
            f"[bold green]Success: Saved run.json, run.csv, and summary.md inside {output_dir.name}/ folder.[/bold green]"
        )
        return 0
