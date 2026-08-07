"""
CLI benchmark command.

Author: Antigravity
License: MIT
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mlos.benchmark.framework import BenchmarkRunner
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine


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

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos benchmark data.csv\n"
            "  mlos benchmark dataset1.csv dataset2.csv --output-dir reports/benchmark"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "datasets",
            nargs="*",
            help="Paths to dataset CSV files.",
        )
        parser.add_argument(
            "--output-dir",
            default="benchmark",
            help="Directory to save benchmark report outputs (run.json, run.csv, summary.md).",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()

        proj_root = find_project_root()
        datasets = args.datasets
        if not datasets:
            root_dir = proj_root or Path.cwd()
            sample_candidates = [
                root_dir / "sample.csv",
                root_dir / "data" / "sample.csv",
                Path.cwd() / "sample.csv",
            ]
            found_csv = next((p for p in sample_candidates if p.is_file()), None)
            if found_csv:
                datasets = [str(found_csv)]
            else:
                console.print(
                    "[bold red]Error: No datasets specified. Please provide dataset CSV path(s).[/bold red]\n"
                    "[bold yellow]Suggested fix: Pass dataset paths as arguments, e.g., 'mlos benchmark data.csv'[/bold yellow]"
                )
                return 1

        output_path = Path(args.output_dir)
        if not output_path.is_absolute():
            output_dir = (
                (proj_root / output_path) if proj_root else (Path.cwd() / output_path)
            )
        else:
            output_dir = output_path

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
                console.print(
                    "[bold yellow]Suggested fix: Ensure dataset files exist and are valid CSV files with readable contents.[/bold yellow]"
                )
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
