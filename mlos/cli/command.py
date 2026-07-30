"""
Base command specification.

Author: Vikram Tanakala
License: MIT
"""
from abc import ABC, abstractmethod
import argparse
from mlos.engine.engine import MLOSEngine


class BaseCommand(ABC):
    """
    Base class for all ML-OS CLI command handlers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name as invoked by the user."""
        pass

    @property
    @abstractmethod
    def help(self) -> str:
        """The help text describing this command."""
        pass

    @abstractmethod
    def register_args(self, parser: argparse.ArgumentParser) -> None:
        """Register subcommand-specific arguments."""
        pass

    @abstractmethod
    def handle(self, args: argparse.Namespace, engine: MLOSEngine) -> int:
        """
        Execute the command.
        Returns:
            int: The exit code (0 for success, non-zero for error).
        """
        pass
