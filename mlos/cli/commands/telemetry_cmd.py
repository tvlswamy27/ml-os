"""
CLI telemetry command.

Author: Antigravity
License: MIT
"""

import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
)
from mlos.observability.telemetry import TelemetryAggregator


class TelemetryCommand(BaseCommand):
    """
    Displays unified subsystem execution summaries and chronological timelines.
    """

    @property
    def name(self) -> str:
        return "telemetry"

    @property
    def help(self) -> str:
        return "Display unified subsystems telemetry and execution timelines."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()
        if not project_root:
            console.print("[bold red]Error: No active ML-OS project found.[/bold red]")
            return 1

        memory = reconstruct_project_memory(project_root)
        if not memory:
            console.print(
                "[bold red]Error: Failed to load project configuration.[/bold red]"
            )
            return 1

        summary = TelemetryAggregator.get_summary(memory)
        timeline = TelemetryAggregator.compile_timeline(memory)

        console.print(
            Panel(
                f"[bold green]Observability Telemetry Summary: {memory.project_name}[/bold green]\n"
                f"[cyan]Total Cognitive Loop Latency:[/cyan] {summary['total_latency_sec']:.3f} s\n"
                f"[cyan]Total Token Usage:[/cyan] {summary['total_tokens']}\n"
                f"[cyan]Total Estimated Cost:[/cyan] ${summary['total_cost']:.5f}",
                expand=False,
            )
        )

        # Per-subsystem table
        sub_table = Table(title="Per-Subsystem Telemetry Aggregation", expand=False)
        sub_table.add_column("Subsystem", style="magenta")
        sub_table.add_column("Executions Count", style="white")
        sub_table.add_column("Avg Latency", style="green")
        sub_table.add_column("Cache Hit Rate", style="yellow")
        sub_table.add_column("Validation Pass Rate", style="cyan")
        sub_table.add_column("Fallback Frequency", style="red")

        for sub, stats in summary["subsystems"].items():
            sub_table.add_row(
                sub,
                str(stats["count"]),
                f"{stats['avg_latency_sec']:.3f} s",
                f"{stats['cache_hit_rate'] * 100:.1f}%",
                f"{stats['validation_pass_rate'] * 100:.1f}%",
                f"{stats['fallback_frequency'] * 100:.1f}%",
            )
        console.print(sub_table)

        # Timeline table
        if timeline:
            timeline_table = Table(
                title="Chronological Loop Execution Timeline", expand=False
            )
            timeline_table.add_column("Index", style="dim cyan")
            timeline_table.add_column("Subsystem", style="magenta")
            timeline_table.add_column("Start", style="white")
            timeline_table.add_column("Duration", style="green")
            timeline_table.add_column("Provider", style="blue")
            timeline_table.add_column("Model", style="blue")
            timeline_table.add_column("Cache", style="yellow")
            timeline_table.add_column("Validation", style="cyan")
            timeline_table.add_column("Fallback", style="red")

            for idx, event in enumerate(timeline):
                timeline_table.add_row(
                    str(idx + 1),
                    event["subsystem"],
                    event["start"].split("T")[1][:8],  # only show time part
                    f"{event['duration']:.3f} s",
                    event["provider"],
                    event["model"],
                    event["cache"],
                    event["validation"],
                    event["fallback"],
                )
            console.print(timeline_table)

        return 0
