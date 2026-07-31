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
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus


class KnowledgeCommand(BaseCommand):
    """
    Consolidates learning updates, version promoted entries, and display current registry status.
    """

    @property
    def name(self) -> str:
        return "knowledge"

    @property
    def help(self) -> str:
        return "Manage persistent policies, conflicts, versions, and promotions."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rule",
            action="store_true",
            help="Use rule-based knowledge algorithm (baseline)",
        )
        group.add_argument(
            "--llm",
            action="store_true",
            help="Use LLM-powered knowledge algorithm",
        )
        group.add_argument(
            "--hybrid",
            action="store_true",
            help="Use hybrid rule/LLM knowledge algorithm",
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

        # Determine knowledge algorithm
        from mlos.planning.config import AlgorithmMode, get_planner_config
        from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
            RuleBasedKnowledgeAlgorithm,
        )
        from mlos.knowledge.algorithms.llm_knowledge_algorithm import (
            LLMKnowledgeAlgorithm,
        )
        from mlos.knowledge.algorithms.hybrid_knowledge_algorithm import (
            HybridKnowledgeAlgorithm,
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

        from mlos.knowledge.algorithms.knowledge_algorithm import KnowledgeAlgorithm

        algo: KnowledgeAlgorithm
        if mode == AlgorithmMode.RULE:
            algo = RuleBasedKnowledgeAlgorithm()
        elif mode == AlgorithmMode.LLM:
            algo = LLMKnowledgeAlgorithm()
        elif mode == AlgorithmMode.HYBRID:
            algo = HybridKnowledgeAlgorithm()

        engine.knowledge_engine.knowledge_algorithm = algo
        engine.project_memory = memory

        with console.status(
            f"[bold green]Syncing persistent system knowledge using {mode.value} algorithm...[/bold green]"
        ):
            try:
                session = engine.manage_knowledge()
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(f"[bold red]Knowledge management failed: {e}[/bold red]")
                return 1

        console.print(
            Panel(
                f"[bold green]Knowledge Sync Complete: {memory.project_name}[/bold green]",
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

        promotion_count = len(session.promoted_entries)
        new_versions = sum(
            1 for e in session.promoted_entries if e.version.version_number > 1
        )
        deprecated_count = sum(
            1
            for e in session.promoted_entries
            if e.status == KnowledgeStatus.DEPRECATED
        )
        conflict_count = len(session.conflicts)

        console.print(
            f"[bold cyan]Promotion Decisions Count:[/bold cyan] {promotion_count}"
        )
        console.print(
            f"[bold cyan]Conflicts Audited Count:[/bold cyan] {conflict_count}"
        )
        console.print(
            f"[bold cyan]Created Entries Count:[/bold cyan] {promotion_count}"
        )
        console.print(
            f"[bold cyan]Deprecated Entries Count:[/bold cyan] {deprecated_count}"
        )
        console.print(f"[bold cyan]Version Updates Count:[/bold cyan] {new_versions}")

        console.print(f"\n[bold cyan]Summary:[/bold cyan] {session.summary}")

        # Active entries
        active_entries = [
            e for e in memory.knowledge_entries if e.status == KnowledgeStatus.ACTIVE
        ]
        if active_entries:
            table = Table(title="Active Persistent Policies (ACTIVE)", expand=False)
            table.add_column("Entry ID", style="dim cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Subsystem", style="blue")
            table.add_column("Component", style="white")
            table.add_column("Version", style="green")
            table.add_column("Parent ID", style="yellow")
            table.add_column("Usage Count", style="cyan")
            table.add_column("Last Used", style="cyan")
            table.add_column("Consumed By", style="blue")
            table.add_column("Parameters", style="green")
            for entry in active_entries:
                subsystems_consumed = ""
                if entry.usage_metadata:
                    subsystems_consumed = entry.usage_metadata.get("subsystems", "")

                table.add_row(
                    entry.knowledge_id[:8] + "...",
                    entry.knowledge_type.value,
                    entry.target_subsystem,
                    entry.target_component,
                    str(entry.version.version_number),
                    (
                        (entry.version.parent_entry_id[:8] + "...")
                        if entry.version.parent_entry_id
                        else "None"
                    ),
                    str(entry.usage_count),
                    entry.last_used.isoformat() if entry.last_used else "Never",
                    subsystems_consumed if subsystems_consumed else "None",
                    str(entry.parameters),
                )
            console.print(table)

        # Experimental entries
        exp_entries = [
            e
            for e in memory.knowledge_entries
            if e.status == KnowledgeStatus.EXPERIMENTAL
        ]
        if exp_entries:
            table = Table(title="Experimental Policies (EXPERIMENTAL)", expand=False)
            table.add_column("Entry ID", style="dim cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Component", style="white")
            table.add_column("Confidence Score", style="green")
            for entry in exp_entries:
                table.add_row(
                    entry.knowledge_id[:8] + "...",
                    entry.knowledge_type.value,
                    entry.target_component,
                    f"{entry.confidence.score:.2f}",
                )
            console.print(table)

        # Deprecated entries
        dep_entries = [
            e
            for e in memory.knowledge_entries
            if e.status == KnowledgeStatus.DEPRECATED
        ]
        if dep_entries:
            table = Table(title="Superseded History Archive (DEPRECATED)", expand=False)
            table.add_column("Entry ID", style="dim cyan")
            table.add_column("Component", style="white")
            table.add_column("Version", style="green")
            table.add_column("Parent ID", style="yellow")
            for entry in dep_entries:
                table.add_row(
                    entry.knowledge_id[:8] + "...",
                    entry.target_component,
                    str(entry.version.version_number),
                    (
                        (entry.version.parent_entry_id[:8] + "...")
                        if entry.version.parent_entry_id
                        else "None"
                    ),
                )
            console.print(table)

        # Conflicts Display
        if session.conflicts:
            table = Table(title="Conflicts Audited and Resolved", expand=False)
            table.add_column("Conflict ID", style="dim cyan")
            table.add_column("Component", style="white")
            table.add_column("Parameter", style="yellow")
            table.add_column("Competing Options", style="red")
            table.add_column("Resolution Applied", style="green")
            for c in session.conflicts:
                table.add_row(
                    c.conflict_id[:8] + "...",
                    c.component,
                    c.parameter_name,
                    ", ".join(c.competing_values),
                    c.resolution_applied,
                )
            console.print(table)

        return 0
