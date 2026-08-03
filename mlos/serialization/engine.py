"""
SerializationEngine combining registry and migration mechanisms.

Author: Antigravity
License: MIT
"""

import json
from typing import Any, Type
import yaml
from mlos.serialization.version import SchemaVersion
from mlos.serialization.registry import SerializationRegistry
from mlos.serialization.migration import MigrationManager


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

        # Inject version meta header
        data["schema_version"] = str(schema_version)
        data["model_class_name"] = model.__class__.__name__

        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            return yaml.safe_dump(data, sort_keys=False)

    def deserialize(
        self,
        data_str: str,
        model_class: Type[Any],
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
