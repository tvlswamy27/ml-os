"""
SchemaVersion and VersionedSerializer classes.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SchemaVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str) -> "SchemaVersion":
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 1
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return cls(major, minor, patch)


class VersionedSerializer(ABC):
    """Abstract interface for all versioned model serializers."""

    @abstractmethod
    def serialize(self, model: Any) -> dict[str, Any]:
        """Convert a model instance to a dictionary representation."""
        pass

    @abstractmethod
    def deserialize(self, data: dict[str, Any]) -> Any:
        """Convert a dictionary representation back to a model instance."""
        pass
