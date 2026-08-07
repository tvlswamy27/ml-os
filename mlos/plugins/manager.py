"""
ML-OS Manifest-Based Plugin System.

Author: Antigravity
License: MIT
"""

import importlib.util
import sys
from enum import Enum
from pathlib import Path
from typing import Any


class PluginType(str, Enum):
    """
    Supported categories of ML-OS plugins.
    """

    PLANNING = "PLANNING"
    DECISION = "DECISION"
    REFLECTION = "REFLECTION"
    LEARNING = "LEARNING"
    KNOWLEDGE = "KNOWLEDGE"
    PROVIDER = "PROVIDER"
    VALIDATOR = "VALIDATOR"
    TRANSLATOR = "TRANSLATOR"
    PROMPT_PACK = "PROMPT_PACK"
    DATASET = "DATASET"
    BENCHMARK = "BENCHMARK"
    CLI_EXTENSION = "CLI_EXTENSION"


class PluginRegistry:
    """
    Singleton manager responsible for plugin discovery, manifest verification, and loading.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_registry()
        return cls._instance

    def _init_registry(self) -> None:
        self.plugins: dict[str, dict[str, Any]] = {}
        self.loaded_classes: dict[PluginType, dict[str, Any]] = {
            pt: {} for pt in PluginType
        }
        self.compatible_versions = ["2.0", "2.1", "2.2"]

    def clear(self) -> None:
        """Resets the registry state for testing."""
        self._init_registry()

    def register_plugin(self, module_path: Path) -> bool:
        """
        Loads a Python file, validates its PLUGIN_INFO manifest,
        and registers the entry point class/function.
        """
        if not module_path.is_file() or module_path.suffix != ".py":
            return False

        module_name = module_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(module_path))
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 1. Retrieve PLUGIN_INFO manifest
            manifest = getattr(module, "PLUGIN_INFO", None)
            if not manifest or not isinstance(manifest, dict):
                return False

            # 2. Check manifest fields
            required_fields = [
                "name",
                "version",
                "type",
                "author",
                "mlos_version",
                "entry_point",
            ]
            if not all(field in manifest for field in required_fields):
                return False

            # Validate type
            try:
                ptype = PluginType(manifest["type"])
            except ValueError:
                # Incompatible plugin type
                return False

            # Validate mlos compatibility
            mlos_ver = manifest["mlos_version"]
            is_compatible = any(
                mlos_ver.startswith(ver) for ver in self.compatible_versions
            )
            if not is_compatible:
                return False

            # 3. Retrieve and resolve entry point
            entry_point_name = manifest["entry_point"]
            resolved_entry = getattr(module, entry_point_name, None)
            if resolved_entry is None:
                return False

            # Register
            plugin_name = manifest["name"]
            self.plugins[plugin_name] = manifest
            self.loaded_classes[ptype][plugin_name] = resolved_entry
            return True

        except Exception:
            return False

    def discover_plugins(self, directory: Path) -> int:
        """
        Scans a directory for plugins and returns the number of successfully registered plugins.
        """
        if not directory.exists() or not directory.is_dir():
            return 0

        registered_count = 0
        for entry in directory.iterdir():
            if entry.is_file() and entry.suffix == ".py":
                if self.register_plugin(entry):
                    registered_count += 1
            elif entry.is_dir():
                # Check for an __init__.py or scan the directory recursively
                registered_count += self.discover_plugins(entry)

        return registered_count

    def get_plugin_class(self, ptype: PluginType, name: str) -> Any:
        """
        Returns a loaded plugin entry point.
        """
        return self.loaded_classes[ptype].get(name)
