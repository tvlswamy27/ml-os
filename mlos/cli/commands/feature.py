"""
CLI Feature command.

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


class FeatureCommand(BaseCommand):
    """
    Command to run the feature intelligence subsystem on the active project.
    """

    @property
    def name(self) -> str:
        return "feature"

    @property
    def help(self) -> str:
        return "Discover, profile, rank, and select dataset features."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rule",
            action="store_true",
            help="Use rule-based feature algorithm (baseline)",
        )
        group.add_argument(
            "--llm",
            action="store_true",
            help="Use LLM-powered feature algorithm",
        )
        group.add_argument(
            "--hybrid",
            action="store_true",
            help="Use hybrid rule/LLM feature algorithm",
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

        if not memory.dataset:
            console.print(
                "[bold red]Error: No dataset has been analyzed yet. Run 'mlos analyze <dataset_path>' first.[/bold red]"
            )
            return 1

        # Determine feature algorithm mode
        from mlos.feature_intelligence.algorithms.feature_algorithm import (
            FeatureAlgorithm,
        )
        from mlos.feature_intelligence.algorithms.rule_based_feature_algorithm import (
            RuleBasedFeatureAlgorithm,
        )
        from mlos.feature_intelligence.algorithms.llm_feature_algorithm import (
            LLMFeatureAlgorithm,
        )
        from mlos.feature_intelligence.algorithms.hybrid_feature_algorithm import (
            HybridFeatureAlgorithm,
        )

        algo: FeatureAlgorithm
        if args.rule:
            mode_name = "Rule-based"
            algo = RuleBasedFeatureAlgorithm()
        elif args.llm:
            mode_name = "LLM"
            algo = LLMFeatureAlgorithm()
        elif args.hybrid:
            mode_name = "Hybrid"
            algo = HybridFeatureAlgorithm()
        else:
            mode_name = "Rule-based"
            algo = RuleBasedFeatureAlgorithm()

        engine.feature_service.feature_engine.feature_algorithm = algo
        engine.project_memory = memory

        with console.status(
            f"[bold green]Running Feature Intelligence using {mode_name} engine...[/bold green]"
        ):
            try:
                session = engine.analyze_features()
                update_project_config_from_memory(project_root, engine.project_memory)
            except Exception as e:
                console.print(
                    f"[bold red]Failed to execute Feature Intelligence: {e}[/bold red]"
                )
                import traceback

                traceback.print_exc()
                return 1

        # Summary output
        console.print(
            Panel(
                f"[bold green]Feature Intelligence Analysis Complete for Project: {memory.project_name}[/bold green]",
                expand=False,
            )
        )

        console.print(f"[bold cyan]Selected Algorithm Mode:[/bold cyan] {mode_name}")
        console.print(
            f"[bold cyan]Number of Insights Detected:[/bold cyan] {len(session.insights)}"
        )
        console.print(
            f"[bold cyan]Number of Recommendations Generated:[/bold cyan] {len(session.recommendations)}"
        )

        # Print Feature profiles
        profile_table = Table(title="Feature Profiles & Statistics")
        profile_table.add_column("Column", justify="left", style="cyan")
        profile_table.add_column("Type", justify="center", style="green")
        profile_table.add_column("Missing %", justify="right")
        profile_table.add_column("Outlier %", justify="right")
        profile_table.add_column("Entropy", justify="right")
        profile_table.add_column("Quality Score", justify="right", style="yellow")
        profile_table.add_column(
            "Action Recommended", justify="center", style="bold magenta"
        )

        # Map recommendations for easy lookup
        rec_map = {
            rec.target_columns[0]: rec
            for rec in session.recommendations
            if rec.target_columns
        }

        for col, profile in session.reasoning_state.feature_profiles.items():
            rec = rec_map.get(col)
            rec_action = rec.action.value if rec else "N/A"
            profile_table.add_row(
                col,
                profile.feature_type.value,
                f"{profile.statistics.missing_percentage:.1%}",
                f"{profile.statistics.outlier_percentage:.1%}",
                f"{profile.statistics.entropy:.2f}",
                f"{profile.quality_score.overall_score:.2f}",
                rec_action,
            )

        console.print(profile_table)

        # Print insights
        if session.insights:
            console.print("\n[bold yellow]Detected Feature Insights:[/bold yellow]")
            for insight in session.insights:
                severity_color = (
                    "red" if insight.severity in ("HIGH", "CRITICAL") else "yellow"
                )
                console.print(
                    f" - [{severity_color}]{insight.severity}[/{severity_color}] [bold]{insight.insight_type}:[/bold] {insight.summary} ({insight.explanation})"
                )

        # Print feature engineering proposals
        if session.engineering_proposals:
            prop_table = Table(title="Feature Engineering Proposals")
            prop_table.add_column("Source Column(s)", justify="left", style="cyan")
            prop_table.add_column("Generated Feature", justify="left", style="green")
            prop_table.add_column("Transformation", justify="center")
            prop_table.add_column("Expected Gain", justify="right", style="yellow")
            prop_table.add_column("Cost", justify="center", style="bold magenta")

            for prop in session.engineering_proposals:
                prop_table.add_row(
                    ", ".join(prop.source_columns),
                    prop.generated_feature,
                    prop.transformation,
                    f"+{prop.expected_gain:.2f}",
                    prop.computational_cost,
                )
            console.print(prop_table)

        # Print consensus ranking
        if session.consensus_ranking:
            console.print("\n[bold cyan]Consensus Feature Ranking (RRF):[/bold cyan]")
            ranking_list = ", ".join(session.consensus_ranking)
            console.print(f" {ranking_list}")

        return 0
