"""
YAML storage.

Handles reading and writing YAML files.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-not-found]


class YamlStorage:
    """
    Handles YAML file operations.
    """

    def save(self, file_path: Path, data: dict[str, Any]) -> None:
        """
        Save a dictionary to a YAML file.

        Args:
            file_path: Destination YAML file.
            data: Dictionary to save.
        """

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                sort_keys=False,
                allow_unicode=True,
            )

    def load(self, file_path: Path) -> dict[str, Any]:
        """
        Load a YAML file.

        Args:
            file_path: YAML file.

        Returns:
            Dictionary containing the YAML contents.
        """

        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}