"""
CLI commands module.

Author: Vikram Tanakala
License: MIT
"""
from mlos.cli.commands.init import InitCommand
from mlos.cli.commands.analyze import AnalyzeCommand
from mlos.cli.commands.run import RunCommand
from mlos.cli.commands.doctor import DoctorCommand

# Explicit command registry for initial release
COMMANDS = [
    InitCommand(),
    AnalyzeCommand(),
    RunCommand(),
    DoctorCommand(),
]

__all__ = ["COMMANDS"]
