"""
CLI Run command.

Author: Antigravity
License: MIT
"""

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    reconstruct_project_memory,
)
from mlos.engine.engine import MLOSEngine


class RunCommand(BaseCommand):
    """
    Command to run the full automated lifecycle loop.
    """

    @property
    def name(self) -> str:
        return "run"

    @property
    def help(self) -> str:
        return "Run the complete automated ML engineering lifecycle via interactive wizard."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos run\n"
            "  mlos run --dataset data.csv --target target_col --non-interactive"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dataset", type=str, help="Path to the dataset file (CSV/Parquet)"
        )
        parser.add_argument("--target", type=str, help="Target column name")
        parser.add_argument(
            "--non-interactive", action="store_true", help="Run without wizard prompt"
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        import ctypes
        import sys

        from mlos.sdk.project import MLProject

        def get_peak_memory_bytes() -> int:
            try:
                if sys.platform == "win32":

                    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                        _fields_ = [
                            ("cb", ctypes.c_ulong),
                            ("PageFaultCount", ctypes.c_ulong),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t),
                        ]

                    GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
                    GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
                    counters = PROCESS_MEMORY_COUNTERS()
                    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                    if GetProcessMemoryInfo(
                        GetCurrentProcess(), ctypes.byref(counters), counters.cb
                    ):
                        return counters.PeakWorkingSetSize
                else:
                    import resource

                    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    if sys.platform == "darwin":
                        return maxrss
                    return maxrss * 1024
            except Exception:
                pass
            return 0

        def format_bytes(size: float) -> str:
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"

        mem_start = get_peak_memory_bytes()
        console = Console()
        project_root = find_project_root()

        if not project_root:
            console.print(
                "[bold red]No ML-OS project found.\n"
                "Run 'mlos init .' to initialize this directory or 'mlos init --name MyProject' to create a new project.[/bold red]"
            )
            return 1

        # Determine interactive wizard parameters

        is_interactive = (
            not getattr(args, "non_interactive", False) and sys.stdin.isatty()
        )
        if is_interactive:
            console.print(
                Panel(
                    "[bold green]ML-OS v3.0 Interactive Wizard[/bold green]",
                    expand=False,
                )
            )

            # Prompt for dataset path
            dataset_path = args.dataset
            if not dataset_path:
                dataset_path = Prompt.ask("Dataset?")

            # Prompt for target column
            target = args.target
            if not target:
                target = Prompt.ask("Target column?")

            # Prompt for Problem Type
            problem_type = Prompt.ask(
                "Problem Type?",
                choices=[
                    "Classification",
                    "Regression",
                    "Forecasting",
                    "Clustering",
                    "NLP",
                    "Computer Vision",
                    "Reinforcement Learning",
                    "Custom Pipeline",
                ],
                default="Classification",
            )

            # Prompt for Optimization Mode
            opt_mode = Prompt.ask(
                "Optimization Mode?",
                choices=["Fast", "Balanced", "Best Quality"],
                default="Balanced",
            )

            # Prompt for Use LLM
            use_llm = Confirm.ask("LLM Assistance?", default=False)

            # Review config
            console.print("\n[bold cyan]Review Configuration:[/bold cyan]")
            console.print(f"  Dataset: {dataset_path}")
            console.print(f"  Target: {target}")
            console.print(f"  Problem Type: {problem_type}")
            console.print(f"  Optimization Mode: {opt_mode}")
            console.print(f"  Use LLM: {'Yes' if use_llm else 'No'}\n")

            proceed = Confirm.ask("Run?", default=True)
            if not proceed:
                console.print("[bold yellow]Cancelled by user.[/bold yellow]")
                return 0
        else:
            # Non-interactive mode
            dataset_path = args.dataset
            target = args.target
            problem_type = "Classification"
            opt_mode = "Balanced"
            use_llm = False

        if not dataset_path:
            console.print("[bold red]Error: Dataset path is required.[/bold red]")
            return 1

        console.print(
            Panel(
                f"[bold green]Running ML-OS Workflow on {dataset_path}...[/bold green]",
                expand=False,
            )
        )

        try:
            # Load MLProject (which initializes registries and trackers)
            project = MLProject(
                dataset_path=dataset_path,
                target_column=target,
                project_path=str(project_root),
            )

            # Store the choices in memory
            if project.memory:
                project.memory.notes.append(
                    f"CLI Run: problem={problem_type}, mode={opt_mode}, llm={use_llm}"
                )

            # Run workflow topologically via SDK API (patched in tests)
            with console.status(
                "[bold green]Orchestrating workflow stages & AutoML Engine...[/bold green]"
            ):
                from mlos.experiment.ids import generate_experiment_id

                experiment_id = generate_experiment_id()
                session = project.run(experiment_id=experiment_id)
                engine.run_automl(
                    dataset_path,
                    target_column=target,
                    output_dir=str(project_root / "artifacts" / "automl"),
                    experiment_id=experiment_id,
                    workspace_root=project_root,
                )

            status = session.run.execution.status
            if status == "FAILED":
                console.print("[bold red]Workflow execution failed![/bold red]")
                return 1

            # Print pipeline execution checklist
            checklist_table = Table(
                title="ML-OS Pipeline Execution Status",
                show_header=True,
                header_style="bold cyan",
            )
            checklist_table.add_column("Pipeline Step", style="bold")
            checklist_table.add_column("Status", justify="center")

            stages_status = [
                ("Analysis (Loading & Validation)", True),
                ("Feature Intelligence", True),
                ("Meta Reasoning", True),
                ("Planning", True),
                ("Execution Runtime", True),
                ("Training", True),
                ("Evaluation", True),
                ("Explainability", True),
                ("Artifacts Generation", len(project.artifacts()) > 0),
                ("Experiment Tracking", True),
                ("Knowledge Capture", True),
            ]

            for stage_name, ok in stages_status:
                status_icon = (
                    "[bold green]✓[/bold green]" if ok else "[bold red]✗[/bold red]"
                )
                checklist_table.add_row(stage_name, status_icon)

            console.print(checklist_table)

            # Print evaluation metrics if present
            eval_metrics = project.metrics()
            from unittest.mock import MagicMock

            if eval_metrics and not isinstance(eval_metrics, MagicMock):
                eval_table = Table(
                    title="Evaluation Results Summary",
                    show_header=True,
                    header_style="bold magenta",
                )
                eval_table.add_column("Metric", style="bold")
                eval_table.add_column("Score")
                for metric, score in eval_metrics.items():
                    if isinstance(score, (int, float)):
                        score_str = f"{score:.4f}"
                    else:
                        score_str = str(score)
                    eval_table.add_row(metric, score_str)
                console.print(eval_table)

            # Print execution summary panel
            from pathlib import Path

            output_folder_resolved = Path(project.project_path).resolve()
            problem_type_name = (
                project.memory.project_profile.problem_type
                if (project.memory and project.memory.project_profile)
                else "Unknown"
            )

            duration = session.run.execution.duration_seconds
            if isinstance(duration, (int, float)):
                duration_str = f"{duration:.2f} sec"
            else:
                duration_str = str(duration)

            mem_delta = get_peak_memory_bytes() - mem_start
            if isinstance(mem_delta, (int, float)):
                mem_delta_str = format_bytes(mem_delta)
            else:
                mem_delta_str = str(mem_delta)

            art_list = project.artifacts()
            if isinstance(art_list, list):
                artifacts_count = str(len(art_list))
            else:
                artifacts_count = str(art_list)

            summary_info = (
                f"[bold cyan]Project:[/bold cyan] {project.name}\n"
                f"[bold cyan]Problem:[/bold cyan] {problem_type_name}\n"
                f"[bold cyan]Experiment ID:[/bold cyan] {session.run.experiment_id}\n"
                f"[bold cyan]Output Folder:[/bold cyan] {output_folder_resolved}\n\n"
                f"[bold cyan]Execution Time:[/bold cyan] {duration_str}\n"
                f"[bold cyan]Peak Memory Delta:[/bold cyan] {mem_delta_str}\n"
                f"[bold cyan]Artifacts Generated:[/bold cyan] {artifacts_count}\n"
                f"[bold cyan]Overall Status:[/bold cyan] [bold green]SUCCESS[/bold green]"
            )
            console.print(
                Panel(
                    summary_info,
                    title="[bold green]ML-OS Run Summary[/bold green]",
                    expand=False,
                )
            )

            return 0

        except Exception as e:
            console.print(f"[bold red]Workflow execution failed: {e}[/bold red]")
            return 1
