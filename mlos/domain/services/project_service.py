"""
Project Service.

Responsible for creating ML projects.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path


class ProjectService:

    def create_project(
        self,
        name: str,
    ) -> Path:

        project_root = Path("playground") / name

        folders = [

            "data",

            "notebooks",

            "models",

            "reports",

            "artifacts",

            ".mlos",

        ]

        project_root.mkdir(parents=True, exist_ok=True)

        for folder in folders:
            (project_root / folder).mkdir(exist_ok=True)

        return project_root