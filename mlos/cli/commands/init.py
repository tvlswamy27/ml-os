"""
CLI Init command.

Author: Vikram Tanakala
License: MIT
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import save_project_config
from mlos.engine.engine import MLOSEngine


class InitCommand(BaseCommand):
    """
    Command to initialize a new ML-OS project workspace.
    """

    @property
    def name(self) -> str:
        return "init"

    @property
    def help(self) -> str:
        return "Initialize a new ML-OS project workspace."

    @property
    def epilog(self) -> str:
        return (
            "Examples:\n"
            "  mlos init .\n"
            "  mlos init --name Demo --goal 'Maximize F1 Score'\n"
            "  mlos init --destination ./my_workspace --non-interactive"
        )

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "path",
            nargs="?",
            default=None,
            help="Target directory (e.g. '.' or 'MyProject')",
        )
        parser.add_argument("--name", type=str, help="Name of the project")
        parser.add_argument("--goal", type=str, help="Goal of the project")
        parser.add_argument(
            "--destination",
            "-d",
            type=str,
            help="Destination directory for the project",
        )
        parser.add_argument(
            "--here",
            action="store_true",
            help="Initialize the current working directory as project root",
        )
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Run in non-interactive mode without prompting",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()

        path_arg = getattr(args, "path", None)
        dest_arg = getattr(args, "destination", None)
        here_arg = getattr(args, "here", False)
        name = getattr(args, "name", None)
        goal = getattr(args, "goal", None)
        non_interactive = getattr(args, "non_interactive", False)

        # Determine target destination directory
        target_dir: Path | None = None
        if here_arg or path_arg == ".":
            target_dir = Path.cwd().resolve()
        elif dest_arg:
            target_dir = Path(dest_arg).resolve()
        elif path_arg and path_arg != ".":
            target_dir = Path(path_arg).resolve()
            if not target_dir.is_absolute():
                target_dir = (Path.cwd() / path_arg).resolve()

        if not non_interactive:
            if not name:
                default_name = target_dir.name if target_dir else Path.cwd().name
                name = Prompt.ask(
                    "[bold cyan]Project Name[/bold cyan]", default=default_name
                )
            if not goal:
                goal = Prompt.ask(
                    "[bold cyan]Project Goal[/bold cyan]",
                    default="ML Optimization Goal",
                )
        else:
            if name is None:
                name = target_dir.name if target_dir else Path.cwd().name
            if goal is None:
                goal = "ML Optimization Goal"

        if not target_dir:
            if name and name != ".":
                target_dir = (Path.cwd() / name).resolve()
            else:
                target_dir = Path.cwd().resolve()

        if (target_dir / ".mlos").is_dir():
            console.print(
                f"[bold yellow]Project already initialized at '{target_dir}'.[/bold yellow]"
            )
            return 0

        if not name or not goal:
            console.print(
                "[bold red]Error: Project name and goal are required.[/bold red]"
            )
            return 1

        with console.status(
            f"[bold green]Initializing project '{name}'...[/bold green]"
        ):
            try:
                # Create the project structure using engine
                project_root = engine.create_project(
                    name=name, goal=goal, destination=target_dir
                )

                # Persist the project configuration
                save_project_config(
                    project_root,
                    {
                        "schema_version": "3.0.0",
                        "project_name": name,
                        "project_goal": goal,
                        "current_stage": "Project Initialization",
                        "completed_tasks": [],
                        "notes": [],
                    },
                )
            except Exception as e:
                console.print(f"[bold red]Failed to initialize project: {e}[/bold red]")
                return 1

        console.print(
            f"[bold green]Successfully initialized project '{name}' at '{project_root}'[/bold green]"
        )
        return 0
