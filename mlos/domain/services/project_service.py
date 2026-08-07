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
        name: str | None = None,
        destination: Path | str | None = None,
    ) -> Path:
        if destination:
            project_root = Path(destination).resolve()
        elif name and name != ".":
            project_root = (Path.cwd() / name).resolve()
        else:
            project_root = Path.cwd().resolve()

        folders = [
            "data",
            "notebooks",
            "models",
            "reports",
            "artifacts",
            "deployments",
            "explainability",
            "experiments",
            "telemetry",
            "benchmarks",
            "knowledge",
            ".mlos",
        ]

        project_root.mkdir(parents=True, exist_ok=True)

        for folder in folders:
            (project_root / folder).mkdir(exist_ok=True)

        return project_root
