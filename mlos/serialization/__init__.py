"""
Serialization module initialization exposing the default SerializationEngine.

Author: Antigravity
License: MIT
"""

from mlos.serialization.engine import SerializationEngine
from mlos.serialization.version import SchemaVersion
from mlos.serialization.serializers.project_memory_serializer import (
    ProjectMemorySerializer,
)
from mlos.domain.models.project_memory import ProjectMemory

# Initialize default serialization engine instance
serialization_engine = SerializationEngine()

# Register ProjectMemorySerializer for all known schema versions
v1_0 = SchemaVersion(1, 0, 0)
v2_0 = SchemaVersion(2, 0, 0)
v2_2 = SchemaVersion(2, 2, 0)
v2_3 = SchemaVersion(2, 3, 0)
v3_0 = SchemaVersion(3, 0, 0)

pm_serializer = ProjectMemorySerializer()
serialization_engine.registry.register(ProjectMemory, v1_0, pm_serializer)
serialization_engine.registry.register(ProjectMemory, v2_0, pm_serializer)
serialization_engine.registry.register(ProjectMemory, v2_2, pm_serializer)
serialization_engine.registry.register(ProjectMemory, v2_3, pm_serializer)
serialization_engine.registry.register(ProjectMemory, v3_0, pm_serializer)

# Register incremental migrations (identity or baseline mappings)
serialization_engine.migration_manager.register_migration(
    "ProjectMemory", v1_0, v2_0, lambda data: data
)
serialization_engine.migration_manager.register_migration(
    "ProjectMemory", v2_0, v2_2, lambda data: data
)
serialization_engine.migration_manager.register_migration(
    "ProjectMemory", v2_2, v2_3, lambda data: data
)
serialization_engine.migration_manager.register_migration(
    "ProjectMemory", v2_3, v3_0, lambda data: data
)
