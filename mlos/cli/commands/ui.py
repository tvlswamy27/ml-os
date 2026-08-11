"""
CLI UI command.
Launches the local-first Flask server and opens the default web browser.
"""

import argparse
import sys
import time
import webbrowser
from threading import Thread

from rich.console import Console

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine


class UICommand(BaseCommand):
    """
    Command to start the ML-OS Studio Web Workspace.
    """

    @property
    def name(self) -> str:
        return "ui"

    @property
    def help(self) -> str:
        return "Start the local ML-OS Web UI workspace."

    @property
    def epilog(self) -> str:
        return "Examples:\n" "  mlos ui\n" "  mlos ui --port 8080 --host 0.0.0.0"

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--port",
            "-p",
            type=int,
            default=5000,
            help="Port to run the UI server on (default: 5000)",
        )
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host address to bind the UI server to (default: 127.0.0.1)",
        )

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 5000)

        # Check for flask availability
        try:
            import flask
        except ImportError:
            console.print(
                "[bold red]Flask is required to run the UI.\n"
                'Please install it using: pip install flask or pip install "mlos[ui]"[/bold red]'
            )
            return 1

        # Check project root for informative message
        project_root = find_project_root()
        if project_root:
            console.print(
                f"[bold green]✓ Active ML-OS project workspace discovered at '{project_root}'[/bold green]"
            )
        else:
            console.print(
                "[bold yellow]! No active ML-OS project discovered in current path.[/bold yellow]"
            )
            console.print(
                "[yellow]You can initialize a new project workspace in the web interface.[/yellow]"
            )

        console.print(f"[bold green]Starting ML-OS Studio UI...[/bold green]")
        console.print(
            f"[bold cyan]Running locally at: http://{host}:{port}[/bold cyan]"
        )
        console.print(
            "[yellow]Press Ctrl+C to terminate the UI server session.[/yellow]\n"
        )

        # Open web browser automatically in a daemon thread
        def launch_browser():
            time.sleep(1.2)
            try:
                webbrowser.open(f"http://{host}:{port}")
            except Exception as e:
                console.print(
                    f"[yellow]Could not automatically launch browser: {e}[/yellow]"
                )

        Thread(target=launch_browser, daemon=True).start()

        # Launch Flask application
        try:
            # We import here to prevent importing flask at CLI load time
            from mlos.ui.app import app

            # Disable default flask banner output for cleaner look
            import click

            cli = sys.modules.get("flask.cli")
            if cli:
                cli.show_server_banner = lambda *a, **kw: None  # type: ignore[attr-defined]

            app.run(host=host, port=port, debug=False)
            return 0
        except Exception as e:
            console.print(f"[bold red]UI Server crashed: {e}[/bold red]")
            return 1
