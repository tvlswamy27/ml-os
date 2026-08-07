"""
MigrationManager handling step-by-step schema migrations.

Author: Antigravity
License: MIT
"""

from collections.abc import Callable
from typing import Any

from mlos.serialization.version import SchemaVersion


class MigrationManager:
    """Manages sequential upgrades of dictionary configurations to newer schemas."""

    def __init__(self) -> None:
        # Maps (model_class_name, source_version_str, target_version_str) -> transform_fn
        self._migrations: dict[
            tuple[str, str, str], Callable[[dict[str, Any]], dict[str, Any]]
        ] = {}

    def register_migration(
        self,
        model_class_name: str,
        source: SchemaVersion,
        target: SchemaVersion,
        transform_fn: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Register a transformation step from a source schema to target schema version."""
        self._migrations[(model_class_name, str(source), str(target))] = transform_fn

    def migrate(
        self,
        model_class_name: str,
        data: dict[str, Any],
        current_version: SchemaVersion,
        target_version: SchemaVersion,
    ) -> dict[str, Any]:
        """Runs sequential migration transformations from current_version to target_version."""
        if str(current_version) == str(target_version):
            return data

        # Simple linear migration pathway finder (e.g. 1.0.0 -> 2.0.0 -> 3.0.0)
        curr = current_version
        max_steps = 100
        steps_run = 0

        while str(curr) != str(target_version) and steps_run < max_steps:
            # Look for migrations starting from curr
            found = False
            for (mname, src, dst), fn in self._migrations.items():
                if mname == model_class_name and src == str(curr):
                    data = fn(data)
                    curr = SchemaVersion.parse(dst)
                    found = True
                    break
            if not found:
                # No step found, assume identity migration or raise
                break
            steps_run += 1

        return data
