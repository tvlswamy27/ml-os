"""
CLI Plan command.

Author: Vikram Tanakala
License: MIT
"""

import argparse
from rich.console import Console
from rich.panel import Panel
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    update_project_config_from_memory,
)


class PlanCommand(BaseCommand):
    """
    Command to run the planning subsystem on the active project.
    """

    @property
    def name(self) -> str:
        return "plan"

    @property
    def help(self) -> str:
        return "Generate an execution plan based on current observations."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rule",
            action="store_true",
            help="Use rule-based planning algorithm (baseline)",
        )
        group.add_argument(
            "--llm",
            action="store_true",
            help="Use LLM-powered planning algorithm",
        )
        group.add_argument(
            "--hybrid",
            action="store_true",
            help="Use hybrid rule/LLM planning algorithm",
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

        # Determine planning algorithm
        from mlos.planning.config import AlgorithmMode, get_planner_config
        from mlos.planning.algorithms.rule_based_algorithm import (
            RuleBasedPlanningAlgorithm,
        )
        from mlos.planning.algorithms.llm_planning_algorithm import LLMPlanningAlgorithm
        from mlos.planning.algorithms.hybrid_planning_algorithm import (
            HybridPlanningAlgorithm,
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

        from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm

        algo: PlanningAlgorithm
        if mode == AlgorithmMode.RULE:
            algo = RuleBasedPlanningAlgorithm()
        elif mode == AlgorithmMode.LLM:
            algo = LLMPlanningAlgorithm()
        elif mode == AlgorithmMode.HYBRID:
            algo = HybridPlanningAlgorithm()

        engine.planning_engine.planning_algorithm = algo

        engine.project_memory = memory

        with console.status(
            f"[bold green]Generating execution strategy using {mode.value} planner...[/bold green]"
        ):
            try:
                session = engine.plan()
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(f"[bold red]Failed to execute planning: {e}[/bold red]")
                return 1

        # Summary output
        console.print(
            Panel(
                f"[bold green]Planning Complete for Project: {memory.project_name}[/bold green]",
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

        console.print(
            f"[bold cyan]Number of Hypotheses:[/bold cyan] {len(session.hypotheses)}"
        )

        # Candidate strategies list
        cands_str = (
            ", ".join([c.strategy_name for c in session.candidates])
            if session.candidates
            else "None"
        )
        console.print(f"[bold cyan]Candidate Strategies:[/bold cyan] {cands_str}")

        # Selected execution strategy
        sel = session.selected_execution_strategy
        sel_name = sel.strategy_name if sel else "None"
        console.print(f"[bold cyan]Selected Execution Strategy:[/bold cyan] {sel_name}")

        # Confidence level
        confidence_level = "None"
        if sel and session.candidates:
            for c in session.candidates:
                if c.strategy_name == sel.strategy_name:
                    confidence_level = (
                        c.confidence.confidence_level if c.confidence else "None"
                    )
                    break
        console.print(f"[bold cyan]Confidence Level:[/bold cyan] {confidence_level}")

        return 0
