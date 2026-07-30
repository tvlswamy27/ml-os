"""
CLI Doctor command.

Author: Vikram Tanakala
License: MIT
"""
import argparse
import os
import platform
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from mlos.engine.engine import MLOSEngine
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root, load_project_config


class DoctorCommand(BaseCommand):
    """
    Check the health and environment configuration of ML-OS.
    """

    @property
    def name(self) -> str:
        return "doctor"

    @property
    def help(self) -> str:
        return "Check the health and environment configuration of ML-OS."

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        console.print(
            Panel(
                "[bold green]ML-OS Doctor - Environment Diagnostics[/bold green]",
                expand=False,
            )
        )

        # Check Python Version
        py_version = sys.version_info
        py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        py_ok = py_version.major == 3 and py_version.minor >= 11
        py_status = "[bold green]✓[/bold green]" if py_ok else "[bold red]✗[/bold red]"

        # Check Dependencies
        dependencies = {}
        # Pandas
        try:
            import pandas

            dependencies["pandas"] = (True, getattr(pandas, "__version__", "Installed"))
        except ImportError:
            dependencies["pandas"] = (False, "Not installed")

        # PyYAML
        try:
            import yaml

            dependencies["PyYAML"] = (True, getattr(yaml, "__version__", "Installed"))
        except ImportError:
            dependencies["PyYAML"] = (False, "Not installed")

        # Rich
        try:
            import rich

            dependencies["rich"] = (True, getattr(rich, "__version__", "Installed"))
        except ImportError:
            dependencies["rich"] = (False, "Not installed")

        # Check Project Root
        project_root = find_project_root()
        project_root_str = str(project_root) if project_root else "None"
        project_status = (
            "[bold green]✓ (Found)[/bold green]"
            if project_root
            else "[yellow]? (Not inside a project)[/yellow]"
        )

        # Create diagnostic table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="bold")
        table.add_column("Status")
        table.add_column("Details")

        table.add_row(
            "Python Version >= 3.11", py_status, f"Python {py_version_str}"
        )

        for dep, (ok, ver) in dependencies.items():
            status = "[bold green]✓[/bold green]" if ok else "[bold red]✗[/bold red]"
            table.add_row(f"Dependency: {dep}", status, ver)

        table.add_row("Active ML-OS Project", project_status, project_root_str)

        console.print(table)

        # Print project config summary if inside a project
        if project_root:
            config = load_project_config(project_root)
            if config:
                config_table = Table(
                    title="Active Project Configuration",
                    show_header=True,
                    header_style="bold yellow",
                )
                config_table.add_column("Setting", style="bold")
                config_table.add_column("Value")
                for key, val in config.items():
                    config_table.add_row(key, str(val))
                console.print(config_table)

        # Overall Status
        all_ok = py_ok and all(ok for ok, _ in dependencies.values())
        if all_ok:
            console.print(
                "[bold green]All environment checks passed successfully![/bold green]"
            )
            return 0
        else:
            console.print(
                "[bold red]Some environment checks failed. Please fix the issues above.[/bold red]"
            )
            return 1
