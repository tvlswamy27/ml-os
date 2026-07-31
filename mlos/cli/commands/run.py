"""
CLI Run command.

Author: Vikram Tanakala
License: MIT
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.workflow.workflow_hooks import WorkflowHook
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
    update_project_config_from_memory,
)


class RunCommand(BaseCommand):
    """
    Command to run the full automated lifecycle loop.
    """

    @property
    def name(self) -> str:
        return "run"

    @property
    def help(self) -> str:
        return "Run the complete automated ML engineering lifecycle."

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

        # Setup workflow callbacks for interactive updates
        def before_analysis(path):
            console.print("[bold blue][Info][/bold blue] Starting analysis...")

        def after_analysis(mem):
            console.print(
                "[bold green][Success][/bold green] Dataset analysis complete."
            )
            console.print(
                "[bold blue][Info][/bold blue] Formulating decisions and generating code..."
            )

        def before_execution(mem):
            console.print(
                "[bold blue][Info][/bold blue] Executing the assembled pipeline..."
            )

        def after_execution(mem):
            console.print(
                "[bold green][Success][/bold green] Pipeline execution completed successfully."
            )
            console.print("[bold blue][Info][/bold blue] Evaluating results...")

        engine.hooks.subscribe(WorkflowHook.BEFORE_ANALYSIS, before_analysis)
        engine.hooks.subscribe(WorkflowHook.AFTER_ANALYSIS, after_analysis)
        engine.hooks.subscribe(WorkflowHook.BEFORE_EXECUTION, before_execution)
        engine.hooks.subscribe(WorkflowHook.AFTER_EXECUTION, after_execution)

        console.print(
            Panel(
                f"[bold green]Running ML-OS Workflow on {dataset_path}...[/bold green]",
                expand=False,
            )
        )

        # Run the workflow using the engine
        with console.status(
            "[bold green]Orchestrating workflow stages...[/bold green]"
        ) as status:
            result = engine.run(dataset_path, target)

            # Sync the memory back to the configuration file
            update_project_config_from_memory(project_root, engine.project_memory)

        if result.status == "FAILED":
            console.print("[bold red]Workflow execution failed![/bold red]")
            for step, error in result.errors.items():
                console.print(
                    Panel(f"[bold red]Error in stage '{step}':[/bold red]\n{error}")
                )
            return 1

        console.print(
            Panel(
                "[bold green]✓ Workflow completed successfully![/bold green]",
                expand=False,
            )
        )

        # Display Pipeline and Evaluation details
        mem = engine.project_memory
        if mem.pipeline:
            console.print(
                f"[bold cyan]Pipeline generated at:[/bold cyan] {mem.pipeline.entrypoint_path}"
            )

        if mem.evaluation_result:
            eval_table = Table(
                title="Evaluation Results Summary",
                show_header=True,
                header_style="bold magenta",
            )
            eval_table.add_column("Metric / Check", style="bold")
            eval_table.add_column("Status / Score")

            for metric, score in mem.evaluation_result.metrics.items():
                eval_table.add_row(metric, f"{score:.4f}")
            for check, passed in mem.evaluation_result.checks.items():
                status_str = (
                    "[bold green]PASS[/bold green]"
                    if passed
                    else "[bold red]FAIL[/bold red]"
                )
                eval_table.add_row(f"Check: {check}", status_str)

            console.print(eval_table)

        return 0
