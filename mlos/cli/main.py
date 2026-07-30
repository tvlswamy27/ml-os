"""
CLI Entrypoint.

Author: Vikram Tanakala
License: MIT
"""
import argparse
import sys
from mlos.engine.engine import MLOSEngine
from mlos.cli.commands import COMMANDS


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for ML-OS CLI.
    """
    parser = argparse.ArgumentParser(
        prog="mlos",
        description="ML-OS: Command Line Interface for ML Engineering Orchestration",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    subparsers.required = True

    # Map command name to instance
    command_map = {}
    for cmd in COMMANDS:
        cmd_parser = subparsers.add_parser(cmd.name, help=cmd.help)
        cmd.register_args(cmd_parser)
        command_map[cmd.name] = cmd

    args = parser.parse_args(argv)

    engine = MLOSEngine()

    try:
        active_command = command_map[args.command]
        return active_command.handle(args, engine)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
