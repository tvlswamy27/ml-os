"""
CLI Meta command.

Author: Antigravity
License: MIT
"""

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    update_project_config_from_memory,
)
from mlos.engine.engine import MLOSEngine


class MetaCommand(BaseCommand):
    """
    Command to run the meta-reasoning orchestrator subsystem on the active project.
    """

    @property
    def name(self) -> str:
        return "meta"

    @property
    def help(self) -> str:
        return "Run Meta-Reasoning & Cognitive Orchestrator subsystem."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos meta\n"
            "  mlos meta --dry-run\n"
            "  mlos meta --simulate"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Simulate execution without running subsystems",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry-run verify environment, plugins and memory parameters",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        project_root = find_project_root()

        if not project_root:
            console.print(
                "[bold red]No ML-OS project found.\n"
                "Run 'mlos init .' to initialize this directory or 'mlos init --name MyProject' to create a new project.[/bold red]"
            )
            return 1

        memory = reconstruct_project_memory(project_root)
        if not memory:
            console.print(
                "[bold red]Error: Failed to load project configuration from .mlos/project_config.yaml[/bold red]"
            )
            return 1

        engine.project_memory = memory

        # Compile Context
        context = engine.meta_service.build_context(memory)

        if args.dry_run:
            from mlos.domain.models.meta_reasoning.execution_constraints import (
                ExecutionConstraints,
            )
            from mlos.meta_reasoning.validation.dry_run_verifier import DryRunVerifier
            from mlos.meta_reasoning.validation.execution_plan_validator import (
                ExecutionPlanValidator,
            )

            console.print("[bold green]Executing Dry Run Verification...[/bold green]")
            try:
                # Generate Plan
                plan = engine.meta_planner.algorithm.generate_plan(
                    context, engine.meta_planner.plan(context).reasoning_state
                )
                # Verify
                verifier = DryRunVerifier()
                verifier.verify_environment(plan, context)

                constraints = ExecutionConstraints(
                    max_cost=10.0,
                    max_tokens=1000000,
                    max_latency=100000.0,
                    max_cpu=8.0,
                    max_memory=16384.0,
                    minimum_quality=0.0,
                    maximum_retry_depth=3,
                    must_use_local_models=False,
                    allow_network_calls=True,
                    allow_parallel_execution=True,
                )
                validator = ExecutionPlanValidator()
                validator.validate(plan, constraints)

                console.print(
                    Panel(
                        "[bold green]Dry Run Successful![/bold green]\n"
                        "All provider capability selections, dependency cycles, duplicate nodes, "
                        "plugins, memory and configuration files are fully valid and healthy.",
                        expand=False,
                    )
                )
                return 0
            except Exception as e:
                console.print(f"[bold red]Dry Run Failed: {e}[/bold red]")
                return 1

        if args.simulate:
            from mlos.meta_reasoning.simulation.execution_simulator import (
                ExecutionSimulator,
            )

            console.print(
                "[bold green]Running Orchestration Simulation...[/bold green]"
            )
            try:
                session = engine.orchestrate_cognition()
                plan = session.reasoning_state.execution_plan
                if not plan:
                    console.print(
                        "[bold red]Failed to generate plan inside session.[/bold red]"
                    )
                    return 1

                simulator = ExecutionSimulator()
                report = simulator.simulate(plan, context)

                console.print(
                    Panel(
                        f"[bold green]Simulation Report: {memory.project_name}[/bold green]",
                        expand=False,
                    )
                )
                console.print(
                    f"[bold cyan]Estimated Cost:[/bold cyan] ${report.estimated_cost_usd:.4f}"
                )
                console.print(
                    f"[bold cyan]Estimated Tokens:[/bold cyan] {report.estimated_token_usage}"
                )
                console.print(
                    f"[bold cyan]Estimated Runtime:[/bold cyan] {report.estimated_runtime_ms / 1000.0:.2f} s"
                )
                console.print(
                    f"[bold cyan]Success Probability:[/bold cyan] {report.success_probability * 100.0:.1f}%"
                )
                console.print(
                    f"[bold cyan]Peak Memory Limit:[/bold cyan] {report.resource_utilization.get('memory_mb_peak')} MB"
                )
                return 0
            except Exception as e:
                console.print(f"[bold red]Simulation failed: {e}[/bold red]")
                return 1

        # Direct execution of the scheduler
        console.print(
            "[bold green]Orchestrating Cognition via Meta-Reasoning...[/bold green]"
        )
        try:
            session = engine.orchestrate_cognition()
            plan = session.reasoning_state.execution_plan
            if not plan:
                console.print(
                    "[bold red]Failed to generate plan inside session.[/bold red]"
                )
                return 1

            # Dispatch plan and scheduler
            from mlos.meta_reasoning.communication.execution_event_bus import (
                ExecutionEventBus,
            )
            from mlos.meta_reasoning.dispatchers.execution_dispatcher import (
                ExecutionDispatcher,
            )
            from mlos.meta_reasoning.scheduling.execution_scheduler import (
                ExecutionScheduler,
            )

            event_bus = ExecutionEventBus()
            dispatcher = ExecutionDispatcher(engine, event_bus)
            scheduler = ExecutionScheduler(dispatcher, event_bus)

            snapshot = scheduler.execute_schedule(plan, context)
            engine.project_memory_service.add_execution_snapshot(memory, snapshot)

            update_project_config_from_memory(project_root, engine.project_memory)

            console.print(
                Panel(
                    f"[bold green]Cognitive Orchestration Run Completed Successfully![/bold green]\n"
                    f"Generated Checksum: [cyan]{plan.checksum}[/cyan]",
                    expand=False,
                )
            )

            # Subsystem Policies Table
            table = Table(title="Subsystem Policies")
            table.add_column("Subsystem", justify="left", style="cyan")
            table.add_column("Mode", justify="center", style="green")
            table.add_column("Model/Provider", justify="left", style="magenta")
            table.add_column("Cost Estimate", justify="right", style="yellow")

            for sub, policy in plan.subsystem_policies.items():
                pc = policy.strategy.provider_selection
                table.add_row(
                    sub.value,
                    policy.strategy.algorithm_type.value,
                    pc.model_name if pc else "Rule Baseline",
                    (
                        f"${policy.resources.cost_budget_usd:.4f}"
                        if policy.resources.cost_budget_usd is not None
                        else "$0.0000"
                    ),
                )

            console.print(table)
            return 0
        except Exception as e:
            console.print(f"[bold red]Cognitive Orchestration failed: {e}[/bold red]")
            return 1
