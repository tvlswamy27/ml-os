"""
CLI commands module.

Author: Vikram Tanakala
License: MIT
"""

from mlos.cli.commands.init import InitCommand
from mlos.cli.commands.analyze import AnalyzeCommand
from mlos.cli.commands.run import RunCommand
from mlos.cli.commands.doctor import DoctorCommand
from mlos.cli.commands.plan import PlanCommand
from mlos.cli.commands.reflect import ReflectCommand
from mlos.cli.commands.learn import LearnCommand
from mlos.cli.commands.knowledge import KnowledgeCommand
from mlos.cli.commands.benchmark import BenchmarkCommand
from mlos.cli.commands.telemetry_cmd import TelemetryCommand

# Explicit command registry for initial release
COMMANDS = [
    InitCommand(),
    AnalyzeCommand(),
    RunCommand(),
    DoctorCommand(),
    PlanCommand(),
    ReflectCommand(),
    LearnCommand(),
    KnowledgeCommand(),
    BenchmarkCommand(),
    TelemetryCommand(),
]

__all__ = ["COMMANDS"]
