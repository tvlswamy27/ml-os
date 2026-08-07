"""
SerializationEngine combining registry and migration mechanisms.

Author: Antigravity
License: MIT
"""

import json
from typing import Any

import yaml

from mlos.serialization.migration import MigrationManager
from mlos.serialization.registry import SerializationRegistry
from mlos.serialization.version import SchemaVersion


class SerializationEngine:
    """Consolidated engine to serialize and deserialize versioned domain models."""

    def __init__(self) -> None:
        self.registry = SerializationRegistry()
        self.migration_manager = MigrationManager()

    def serialize(
        self, model: Any, schema_version: SchemaVersion, format: str = "yaml"
    ) -> str:
        """Convert a model instance to a serialized string representation (JSON or YAML)."""
        serializer = self.registry.get_serializer(model.__class__, schema_version)
        if not serializer:
            # Fallback if no specific version serializer is found: assume standard dict conversion
            if hasattr(model, "to_dict"):
                data = model.to_dict()
            else:
                data = dict(model)
        else:
            data = serializer.serialize(model)

        data = self._make_yaml_safe(data)

        # Inject version meta header
        data["schema_version"] = str(schema_version)
        data["model_class_name"] = model.__class__.__name__

        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            return yaml.safe_dump(data, sort_keys=False)

    def _make_yaml_safe(self, obj: Any) -> Any:
        """Recursively convert UUIDs, datetimes, paths, enums, sets to PyYAML safe primitive types."""
        import uuid
        from datetime import datetime
        from enum import Enum
        from pathlib import Path

        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {str(k): self._make_yaml_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._make_yaml_safe(x) for x in obj]
        return obj

    def deserialize(
        self,
        data_str: str,
        model_class: type[Any],
        target_version: SchemaVersion,
        format: str = "yaml",
    ) -> Any:
        """Parse a serialized string back to a model instance, performing migrations if needed."""
        if format.lower() == "json":
            data = json.loads(data_str)
        else:
            data = yaml.safe_load(data_str)

        if not data:
            raise ValueError("Failed to parse configuration: empty data.")

        # Extract schema version header (default to 1.0.0 if not present)
        source_ver_str = data.get("schema_version", "1.0.0")
        source_version = SchemaVersion.parse(source_ver_str)

        # Migrate data step-by-step to target version
        migrated_data = self.migration_manager.migrate(
            model_class.__name__, data, source_version, target_version
        )

        serializer = self.registry.get_serializer(model_class, target_version)
        if not serializer:
            # Fallback if no specific serializer is registered
            if hasattr(model_class, "from_dict"):
                return model_class.from_dict(migrated_data)
            return model_class(
                **{
                    k: v
                    for k, v in migrated_data.items()
                    if k not in ("schema_version", "model_class_name")
                }
            )

        return serializer.deserialize(migrated_data)
