"""
CLI Reflect command.

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
    update_project_config_from_memory,
)


class ReflectCommand(BaseCommand):
    """
    Command to run the reflection subsystem on the active project.
    """

    @property
    def name(self) -> str:
        return "reflect"

    @property
    def help(self) -> str:
        return (
            "Analyze run history, extract insights, and generate structured feedback."
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rule",
            action="store_true",
            help="Use rule-based reflection algorithm (baseline)",
        )
        group.add_argument(
            "--llm",
            action="store_true",
            help="Use LLM-powered reflection algorithm",
        )
        group.add_argument(
            "--hybrid",
            action="store_true",
            help="Use hybrid rule/LLM reflection algorithm",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()

        if not project_root:
            console.print(
                "[bold red]Error: No active ML-OS project found. Run 'mlos init' first.[/bold red]"
            )
            return 1

        memory = reconstruct_project_memory(project_root)
        if not memory:
            console.print(
                "[bold red]Error: Failed to load project configuration from .mlos/project_config.yaml[/bold red]"
            )
            return 1

        # Determine reflection algorithm
        from mlos.planning.config import AlgorithmMode, get_planner_config
        from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
            RuleBasedReflectionAlgorithm,
        )
        from mlos.reflection.algorithms.llm_reflection_algorithm import (
            LLMReflectionAlgorithm,
        )
        from mlos.reflection.algorithms.hybrid_reflection_algorithm import (
            HybridReflectionAlgorithm,
        )

        if args.rule:
            mode = AlgorithmMode.RULE
        elif args.llm:
            mode = AlgorithmMode.LLM
        elif args.hybrid:
            mode = AlgorithmMode.HYBRID
        else:
            mode_str = get_planner_config().get("algorithm", "rule")
            try:
                mode = AlgorithmMode(mode_str)
            except ValueError:
                mode = AlgorithmMode.RULE

        from mlos.reflection.algorithms.reflection_algorithm import (
            ReflectionAlgorithm,
        )

        algo: ReflectionAlgorithm
        if mode == AlgorithmMode.RULE:
            algo = RuleBasedReflectionAlgorithm()
        elif mode == AlgorithmMode.LLM:
            algo = LLMReflectionAlgorithm()
        elif mode == AlgorithmMode.HYBRID:
            algo = HybridReflectionAlgorithm()

        engine.reflection_engine.reflection_algorithm = algo

        engine.project_memory = memory

        with console.status(
            f"[bold green]Executing reflection analysis using {mode.value} reflector...[/bold green]"
        ):
            try:
                session = engine.reflect()
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(f"[bold red]Reflection failed: {e}[/bold red]")
                return 1

        # Summary output panel
        console.print(
            Panel(
                f"[bold green]Reflection Complete for Project: {memory.project_name}[/bold green]",
                expand=False,
            )
        )

        telemetry = session.telemetry
        console.print(f"[bold cyan]Selected Algorithm:[/bold cyan] {mode.value}")
        console.print(
            f"[bold cyan]Provider:[/bold cyan] {telemetry.provider if telemetry else 'N/A'}"
        )
        console.print(
            f"[bold cyan]Model:[/bold cyan] {telemetry.model if telemetry else 'N/A'}"
        )

        cache_status = "HIT" if (telemetry and telemetry.cache_hit) else "MISS"
        console.print(f"[bold cyan]Cache Status:[/bold cyan] {cache_status}")

        latency = f"{telemetry.latency_ms:.2f} ms" if telemetry else "0.00 ms"
        console.print(f"[bold cyan]Latency:[/bold cyan] {latency}")

        fallback_status = "Yes" if (telemetry and telemetry.fallback_used) else "No"
        console.print(f"[bold cyan]Fallback Status:[/bold cyan] {fallback_status}")

        validation_status = (
            "Passed"
            if (telemetry and telemetry.validation_passed)
            else ("Failed" if telemetry else "N/A")
        )
        console.print(f"[bold cyan]Validation Status:[/bold cyan] {validation_status}")

        console.print(f"\n[bold cyan]Summary:[/bold cyan] {session.summary}")

        # Display Insights
        if session.insights:
            ins_table = Table(title="Reflection Insights", expand=False)
            ins_table.add_column("Insight ID", style="dim cyan")
            ins_table.add_column("Type", style="magenta")
            ins_table.add_column("Severity", style="bold red")
            ins_table.add_column("Summary", style="white")
            ins_table.add_column("Confidence", style="yellow")
            for ins in session.insights:
                color_severity = ins.severity
                if ins.severity == "CRITICAL":
                    color_severity = "[bold blink red]CRITICAL[/]"
                ins_table.add_row(
                    ins.insight_id,
                    ins.insight_type,
                    color_severity,
                    ins.summary,
                    f"{ins.confidence:.2f}",
                )
            console.print(ins_table)

        # Display Feedback
        if session.feedback:
            fb_table = Table(title="Structured Feedback", expand=False)
            fb_table.add_column("Feedback ID", style="dim cyan")
            fb_table.add_column("Target Subsystem", style="magenta")
            fb_table.add_column("Target Component", style="white")
            fb_table.add_column("Action Type", style="green")
            fb_table.add_column("Priority", style="bold red")
            fb_table.add_column("Expected Outcome", style="yellow")
            for fb in session.feedback:
                fb_table.add_row(
                    fb.feedback_id,
                    fb.target_subsystem,
                    fb.target_component,
                    fb.action_type,
                    fb.priority,
                    fb.expected_outcome,
                )
            console.print(fb_table)

        # Display Confidence
        conf = session.confidence
        if conf:
            console.print(
                Panel(
                    f"[bold]Confidence Details[/bold]\n"
                    f"[cyan]Score:[/cyan] {conf.score:.2f} | [cyan]Uncertainty:[/cyan] {conf.uncertainty:.2f} | [cyan]Status:[/cyan] {'[bold green]ACCEPTED[/]' if conf.accepted else '[bold red]REJECTED[/]'}\n"
                    f"[cyan]Explanation:[/cyan] {conf.explanation}",
                    expand=False,
                )
            )

        return 0
