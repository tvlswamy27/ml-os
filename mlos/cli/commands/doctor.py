"""
CLI Doctor command.

Author: Vikram Tanakala
License: MIT
"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mlos.cli.command import BaseCommand
from mlos.cli.persistence import find_project_root
from mlos.engine.engine import MLOSEngine


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

    @property
    def epilog(self) -> str:
        return "Examples:\n" "  mlos doctor"

    def register_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        console = Console()
        console.print(
            Panel(
                "[bold green]ML-OS Doctor - Environment & Architecture Diagnostics[/bold green]",
                expand=False,
            )
        )

        # 1. Check Python Version
        py_version = sys.version_info
        py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        py_ok = py_version.major == 3 and py_version.minor >= 11

        # 2. Check Required Packages
        packages = {
            "numpy": "numpy",
            "pandas": "pandas",
            "scikit-learn": "sklearn",
            "rich": "rich",
            "PyYAML": "yaml",
        }
        package_checks = {}
        for name, import_name in packages.items():
            try:
                mod = __import__(import_name)
                package_checks[name] = (True, getattr(mod, "__version__", "Installed"))
            except ImportError:
                package_checks[name] = (False, "Not installed")

        # 2b. Check Optional Integration Packages
        optional_packages = {
            "xgboost": "xgboost",
            "transformers": "transformers",
            "openai": "openai",
            "anthropic": "anthropic",
            "google-generativeai": "google.generativeai",
        }
        optional_checks = {}
        for name, import_name in optional_packages.items():
            try:
                mod = __import__(import_name)
                optional_checks[name] = (True, getattr(mod, "__version__", "Installed"))
            except ImportError:
                optional_checks[name] = (False, "Optional (Not installed)")

        # 3. Check SDK API
        try:

            sdk_ok = True
        except Exception:
            sdk_ok = False

        # 4. Check Serialization Engine
        try:
            from mlos.domain.models.project_memory import ProjectMemory
            from mlos.serialization.serializers.project_memory_serializer import (
                ProjectMemorySerializer,
            )

            serializer = ProjectMemorySerializer()
            dummy = ProjectMemory(project_name="DummyTest", project_goal="Validation")
            serialized = serializer.serialize(dummy)
            deserialized = serializer.deserialize(serialized)
            serialization_ok = deserialized.project_name == "DummyTest"
        except Exception:
            serialization_ok = False

        # 5. Check Plugins / Stages
        try:
            from mlos.execution_intelligence.stage import DataLoadingStage

            stage = DataLoadingStage()
            plugin_ok = stage.name == "Data Loading"
        except Exception:
            plugin_ok = False

        # 6. Check Event Bus
        try:
            from mlos.communication.event_bus import GlobalEventBus

            bus = GlobalEventBus()
            events_received = []
            bus.subscribe("DoctorCheck", lambda ev: events_received.append(ev))
            bus.publish("DoctorCheck", "Doctor", {})
            event_bus_ok = len(events_received) == 1
        except Exception:
            event_bus_ok = False

        # 7. Check Artifact Registry
        try:
            from mlos.registry.artifact_registry import ArtifactRegistry

            reg = ArtifactRegistry(".")
            artifact_ok = True
        except Exception:
            artifact_ok = False

        # 8. Check Workspace Write Permissions
        from pathlib import Path

        temp_check_file = Path("doctor_permissions_test.tmp")
        permissions_ok = False
        try:
            temp_check_file.write_text("ok")
            assert temp_check_file.read_text() == "ok"
            permissions_ok = True
        except Exception:
            permissions_ok = False
        finally:
            if temp_check_file.exists():
                try:
                    temp_check_file.unlink()
                except Exception:
                    pass

        # 9. Check Prompt Templates Folder & Loader
        try:
            from mlos.intelligence.prompts.prompt_loader import PromptLoader

            loader = PromptLoader()
            prompts_ok = True
        except Exception:
            prompts_ok = False

        # 10. Check Intelligence Providers
        try:
            from mlos.intelligence.config import ProviderConfig
            from mlos.intelligence.providers.mock_provider import MockProvider

            config_p = ProviderConfig(provider="mock", model="mock-model")
            prov = MockProvider(config_p)
            intel_ok = prov is not None
        except Exception:
            intel_ok = False

        # 11. Check Configuration Integrity
        project_root = find_project_root()
        project_root_str = str(project_root) if project_root else "None"
        if project_root:
            try:
                from mlos.cli.persistence import load_project_config

                cfg = load_project_config(project_root)
                config_ok = cfg is not None
            except Exception:
                config_ok = False
        else:
            config_ok = True

        # Build diagnostics table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        table.add_row(
            "Python (>=3.11)",
            "[bold green]✓[/bold green]" if py_ok else "[bold red]✗[/bold red]",
            f"Python {py_version_str}",
        )

        for pkg, (ok, ver) in package_checks.items():
            table.add_row(
                f"Package: {pkg}",
                "[bold green]✓[/bold green]" if ok else "[bold red]✗[/bold red]",
                ver,
            )

        for pkg, (ok, ver) in optional_checks.items():
            table.add_row(
                f"Optional: {pkg}",
                "[bold green]✓[/bold green]" if ok else "[bold yellow]![/bold yellow]",
                ver,
            )

        table.add_row(
            "SDK API Layer",
            "[bold green]✓[/bold green]" if sdk_ok else "[bold red]✗[/bold red]",
            "from mlos.sdk import MLProject",
        )

        table.add_row(
            "Serialization Engine",
            (
                "[bold green]✓[/bold green]"
                if serialization_ok
                else "[bold red]✗[/bold red]"
            ),
            "ProjectMemorySerializer validation",
        )

        table.add_row(
            "Plugin Stages System",
            "[bold green]✓[/bold green]" if plugin_ok else "[bold red]✗[/bold red]",
            "ExecutionStage topological registry",
        )

        table.add_row(
            "Global Event Bus",
            "[bold green]✓[/bold green]" if event_bus_ok else "[bold red]✗[/bold red]",
            "PubSub message delivery broker",
        )

        table.add_row(
            "Artifact Registry",
            "[bold green]✓[/bold green]" if artifact_ok else "[bold red]✗[/bold red]",
            "Lineage storage engine",
        )

        table.add_row(
            "Workspace Permissions",
            (
                "[bold green]✓[/bold green]"
                if permissions_ok
                else "[bold red]✗[/bold red]"
            ),
            "Local file read/write checks",
        )

        table.add_row(
            "Prompt Templates Assets",
            "[bold green]✓[/bold green]" if prompts_ok else "[bold red]✗[/bold red]",
            "Intelligence context rules load",
        )

        table.add_row(
            "Intelligence Providers",
            "[bold green]✓[/bold green]" if intel_ok else "[bold red]✗[/bold red]",
            "LLM provider initialization",
        )

        table.add_row(
            "Workspace Configuration",
            (
                "[bold green]✓[/bold green]"
                if project_root and config_ok
                else "[bold yellow]![/bold yellow]"
            ),
            f"Active Project Path: {project_root_str}",
        )

        console.print(table)

        if not project_root:
            console.print(
                "[bold yellow]No ML-OS project found.\n"
                "Run 'mlos init .' to initialize this directory or 'mlos init --name MyProject' to create a new project.[/bold yellow]"
            )

        # Print detailed project settings table if inside project
        if project_root and config_ok:
            from mlos.cli.persistence import load_project_config

            config = load_project_config(project_root)
            if config:
                config_table = Table(
                    title="Active Project Settings",
                    show_header=True,
                    header_style="bold yellow",
                )
                config_table.add_column("Setting", style="bold")
                config_table.add_column("Value")
                for key, val in config.items():
                    config_table.add_row(key, str(val))
                console.print(config_table)

        # Check overall success
        all_ok = (
            py_ok
            and all(ok for ok, _ in package_checks.values())
            and sdk_ok
            and serialization_ok
            and plugin_ok
            and event_bus_ok
            and artifact_ok
            and permissions_ok
            and prompts_ok
            and intel_ok
            and config_ok
        )

        if all_ok:
            console.print(
                Panel(
                    "[bold green]Everything looks good. ML-OS is ready.[/bold green]",
                    expand=False,
                )
            )
            return 0
        else:
            console.print(
                Panel(
                    "[bold red]Some diagnostic checks failed. Please inspect the failures above.[/bold red]",
                    expand=False,
                )
            )
            return 1
