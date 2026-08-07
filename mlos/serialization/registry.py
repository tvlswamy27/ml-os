"""
SerializationRegistry to store version-serializer pairs.

Author: Antigravity
License: MIT
"""

from typing import Any

from mlos.serialization.version import SchemaVersion, VersionedSerializer


class SerializationRegistry:
    """Registry mapping model types and schema versions to specific serializers."""

    def __init__(self) -> None:
        self._serializers: dict[tuple[type[Any], str], VersionedSerializer] = {}

    def register(
        self,
        model_class: type[Any],
        version: SchemaVersion,
        serializer: VersionedSerializer,
    ) -> None:
        """Register a serializer for a specific model class and schema version."""
        self._serializers[(model_class, str(version))] = serializer

    def get_serializer(
        self, model_class: type[Any], version: SchemaVersion
    ) -> VersionedSerializer | None:
        """Retrieve the registered serializer for a model class and version."""
        return self._serializers.get((model_class, str(version)))
