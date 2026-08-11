"""
CLI commands module.

Author: Vikram Tanakala
License: MIT
"""

from mlos.cli.commands.analyze import AnalyzeCommand
from mlos.cli.commands.benchmark import BenchmarkCommand
from mlos.cli.commands.doctor import DoctorCommand
from mlos.cli.commands.experiments_cmd import ExperimentsCommand
from mlos.cli.commands.feature import FeatureCommand
from mlos.cli.commands.init import InitCommand
from mlos.cli.commands.knowledge import KnowledgeCommand
from mlos.cli.commands.learn import LearnCommand
from mlos.cli.commands.lineage_cmd import LineageCommand
from mlos.cli.commands.meta_cmd import MetaCommand
from mlos.cli.commands.pipeline_cmd import PipelineCommand
from mlos.cli.commands.plan import PlanCommand
from mlos.cli.commands.reflect import ReflectCommand
from mlos.cli.commands.registry_cmd import RegistryCommand
from mlos.cli.commands.run import RunCommand
from mlos.cli.commands.telemetry_cmd import TelemetryCommand
from mlos.cli.commands.ui import UICommand

# Explicit command registry for initial release
COMMANDS = [
    InitCommand(),
    AnalyzeCommand(),
    RunCommand(),
    DoctorCommand(),
    FeatureCommand(),
    MetaCommand(),
    PlanCommand(),
    ReflectCommand(),
    LearnCommand(),
    KnowledgeCommand(),
    BenchmarkCommand(),
    TelemetryCommand(),
    ExperimentsCommand(),
    PipelineCommand(),
    RegistryCommand(),
    LineageCommand(),
    UICommand(),
]

__all__ = ["COMMANDS"]
