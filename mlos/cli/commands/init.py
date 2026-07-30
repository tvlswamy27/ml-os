"""
CLI Init command.

Author: Vikram Tanakala
License: MIT
"""
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import save_project_config


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

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--name", type=str, help="Name of the project")
        parser.add_argument("--goal", type=str, help="Goal of the project")
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Run in non-interactive mode without prompting",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        name = args.name
        goal = args.goal

        if not args.non_interactive:
            if not name:
                name = Prompt.ask("[bold cyan]Project Name[/bold cyan]")
            if not goal:
                goal = Prompt.ask("[bold cyan]Project Goal[/bold cyan]")

        if not name or not goal:
            console.print(
                "[bold red]Error: Project name and goal are required.[/bold red]"
            )
            return 1

        with console.status(
            f"[bold green]Initializing project '{name}'...[/bold green]"
        ):
            try:
                # Create the project structure using the engine
                engine.create_project(name=name, goal=goal)

                # Persist the project configurations
                project_root = Path("playground") / name
                save_project_config(
                    project_root,
                    {
                        "project_name": name,
                        "project_goal": goal,
                        "current_stage": "Project Initialization",
                        "completed_tasks": [],
                        "notes": [],
                    },
                )
            except Exception as e:
                console.print(
                    f"[bold red]Failed to initialize project: {e}[/bold red]"
                )
                return 1

        console.print(
            f"[bold green]Successfully initialized project '{name}' at 'playground/{name}'[/bold green]"
        )
        return 0
