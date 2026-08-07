"""
Unit and integration tests for Milestone 1: Unified & Transparent Serialization.

Author: Antigravity
License: MIT
"""

from typing import Any

from mlos.domain.models.project_memory import ProjectMemory
from mlos.serialization.engine import SerializationEngine
from mlos.serialization.migration import MigrationManager
from mlos.serialization.registry import SerializationRegistry
from mlos.serialization.version import SchemaVersion, VersionedSerializer


class DummyModel:
    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value


class DummySerializer(VersionedSerializer):
    def serialize(self, model: DummyModel) -> dict[str, Any]:  # type: ignore[override]
        return {"name": model.name, "value": model.value}

    def deserialize(self, data: dict[str, Any]) -> DummyModel:
        return DummyModel(data["name"], data["value"])


def test_schema_version():
    v1 = SchemaVersion.parse("1.2.3")
    assert v1.major == 1
    assert v1.minor == 2
    assert v1.patch == 3
    assert str(v1) == "1.2.3"

    v2 = SchemaVersion.parse("2.0")
    assert v2.major == 2
    assert v2.minor == 0
    assert v2.patch == 0


def test_serialization_registry():
    registry = SerializationRegistry()
    ver = SchemaVersion(1, 0, 0)
    serializer = DummySerializer()

    registry.register(DummyModel, ver, serializer)
    retrieved = registry.get_serializer(DummyModel, ver)
    assert retrieved is serializer

    retrieved_none = registry.get_serializer(DummyModel, SchemaVersion(2, 0, 0))
    assert retrieved_none is None


def test_migration_manager():
    manager = MigrationManager()
    v1 = SchemaVersion(1, 0, 0)
    v2 = SchemaVersion(2, 0, 0)
    v3 = SchemaVersion(3, 0, 0)

    # Migrate "val" to "value"
    def step1(data: dict) -> dict:
        data["value"] = data.pop("val") * 2
        return data

    # Migrate name prefix
    def step2(data: dict) -> dict:
        data["name"] = f"migrated_{data['name']}"
        return data

    manager.register_migration("DummyModel", v1, v2, step1)
    manager.register_migration("DummyModel", v2, v3, step2)

    old_data = {"name": "test", "val": 10}
    new_data = manager.migrate("DummyModel", old_data, v1, v3)

    assert new_data["name"] == "migrated_test"
    assert new_data["value"] == 20


def test_serialization_engine():
    engine = SerializationEngine()
    ver = SchemaVersion(1, 0, 0)
    serializer = DummySerializer()
    engine.registry.register(DummyModel, ver, serializer)

    model = DummyModel("engine_test", 42)
    yaml_str = engine.serialize(model, ver, format="yaml")
    assert "engine_test" in yaml_str
    assert "1.0.0" in yaml_str

    deserialized = engine.deserialize(yaml_str, DummyModel, ver, format="yaml")
    assert deserialized.name == "engine_test"
    assert deserialized.value == 42

    # Check JSON format
    json_str = engine.serialize(model, ver, format="json")
    deserialized_json = engine.deserialize(json_str, DummyModel, ver, format="json")
    assert deserialized_json.name == "engine_test"
    assert deserialized_json.value == 42


def test_project_memory_transparent_serialization(tmp_path):
    from mlos.cli.persistence import (
        reconstruct_project_memory,
        update_project_config_from_memory,
    )

    memory = ProjectMemory("PersistenceProject", "ValidationGoal")
    update_project_config_from_memory(tmp_path, memory)

    reconstructed = reconstruct_project_memory(tmp_path)
    assert reconstructed is not None
    assert reconstructed.project_name == "PersistenceProject"
    assert reconstructed.project_goal == "ValidationGoal"
