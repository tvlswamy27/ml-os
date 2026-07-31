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


class LearnCommand(BaseCommand):
    """
    Consolidates reflection feedback history and compile permanent machine-readable updates.
    """

    @property
    def name(self) -> str:
        return "learn"

    @property
    def help(self) -> str:
        return "Consume reflection feedback history and compile permanent machine-readable updates."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rule",
            action="store_true",
            help="Use rule-based learning algorithm (baseline)",
        )
        group.add_argument(
            "--llm",
            action="store_true",
            help="Use LLM-powered learning algorithm",
        )
        group.add_argument(
            "--hybrid",
            action="store_true",
            help="Use hybrid rule/LLM learning algorithm",
        )

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

        # Determine learning algorithm
        from mlos.planning.config import AlgorithmMode, get_planner_config
        from mlos.learning.algorithms.rule_based_learning_algorithm import (
            RuleBasedLearningAlgorithm,
        )
        from mlos.learning.algorithms.llm_learning_algorithm import (
            LLMLearningAlgorithm,
        )
        from mlos.learning.algorithms.hybrid_learning_algorithm import (
            HybridLearningAlgorithm,
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

        from mlos.learning.algorithms.learning_algorithm import LearningAlgorithm

        algo: LearningAlgorithm
        if mode == AlgorithmMode.RULE:
            algo = RuleBasedLearningAlgorithm()
        elif mode == AlgorithmMode.LLM:
            algo = LLMLearningAlgorithm()
        elif mode == AlgorithmMode.HYBRID:
            algo = HybridLearningAlgorithm()

        engine.learning_engine.learning_algorithm = algo
        engine.project_memory = memory

        with console.status(
            f"[bold green]Executing learning consolidation using {mode.value} learner...[/bold green]"
        ):
            try:
                session = engine.learn()
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(f"[bold red]Learning failed: {e}[/bold red]")
                return 1

        console.print(
            Panel(
                f"[bold green]Learning Cycle Complete: {memory.project_name}[/bold green]",
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

        proposal_count = len(session.updates)
        accepted_count = (
            len(session.updates)
            if (session.confidence and session.confidence.accepted)
            else 0
        )
        console.print(f"[bold cyan]Proposal Count:[/bold cyan] {proposal_count}")
        console.print(
            f"[bold cyan]Accepted Proposal Count:[/bold cyan] {accepted_count}"
        )

        console.print(f"\n[bold cyan]Summary:[/bold cyan] {session.summary}")

        # Display Updates
        if session.updates:
            table = Table(title="Generated Learning Updates", expand=False)
            table.add_column("Update ID", style="dim cyan")
            table.add_column("Update Type", style="magenta")
            table.add_column("Component", style="white")
            table.add_column("Parameters", style="green")
            table.add_column("Observations", style="yellow")
            for upd in session.updates:
                table.add_row(
                    upd.update_id[:8] + "...",
                    upd.update_type.value,
                    upd.target_component,
                    str(upd.parameters),
                    ", ".join(upd.evidence.supporting_observations),
                )
            console.print(table)

        # Confidence summary
        if session.confidence:
            conf = session.confidence
            console.print(
                Panel(
                    f"[bold]Learning Confidence Details[/bold]\n"
                    f"[cyan]Score:[/cyan] {conf.score:.2f} | [cyan]Uncertainty:[/cyan] {conf.uncertainty:.2f} | [cyan]Status:[/cyan] {'[bold green]ACCEPTED[/]' if conf.accepted else '[bold red]REJECTED[/]'}\n"
                    f"[cyan]Explanation:[/cyan] {conf.explanation}",
                    expand=False,
                )
            )

        return 0
