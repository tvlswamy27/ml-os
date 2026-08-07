"""
Base command specification.

Author: Vikram Tanakala
License: MIT
"""

import argparse
from abc import ABC, abstractmethod

from mlos.engine.engine import MLOSEngine


class BaseCommand(ABC):
    """
    Base class for all ML-OS CLI command handlers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name as invoked by the user."""

    @property
    @abstractmethod
    def help(self) -> str:
        """The help text describing this command."""

    @property
    def description(self) -> str:
        """Detailed description for command help page."""
        return self.help

    @property
    def epilog(self) -> str:
        """Usage examples and additional guidance."""
        return ""

    @abstractmethod
    def register_args(self, parser: argparse.ArgumentParser) -> None:
        """Register subcommand-specific arguments."""

    @abstractmethod
    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        """
        Execute the command.
        Returns:
            int: The exit code (0 for success, non-zero for error).
        """
