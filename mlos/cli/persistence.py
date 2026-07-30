"""
CLI Persistence helper.

Responsible for saving and loading lightweight project configurations.

Author: Vikram Tanakala
License: MIT
"""
import os
from pathlib import Path
import yaml
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """
    Search upwards from start_dir to find a directory containing a '.mlos' folder.
    """
    current = Path(start_dir or os.getcwd()).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".mlos").is_dir():
            return parent
    return None


def load_project_config(project_root: Path) -> dict | None:
    """
    Load project configurations from the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    if not config_file.is_file():
        return None
    with open(config_file, "r") as f:
        return yaml.safe_load(f) or {}


def save_project_config(project_root: Path, config: dict) -> None:
    """
    Save project configurations to the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def reconstruct_project_memory(project_root: Path) -> ProjectMemory | None:
    """
    Reconstruct ProjectMemory from the lightweight config on disk.
    """
    config = load_project_config(project_root)
    if config is None:
        return None

    memory_service = ProjectMemoryService()
    memory = memory_service.create(
        project_name=config.get("project_name", ""),
        project_goal=config.get("project_goal", ""),
    )

    if "current_stage" in config:
        memory.current_stage = config["current_stage"]
    if "completed_tasks" in config:
        memory.completed_tasks = config.get("completed_tasks", [])
    if "notes" in config:
        memory.notes = config.get("notes", [])

    dataset_path = config.get("dataset_path")
    if dataset_path:
        from mlos.domain.models.dataset import Dataset

        dataset = Dataset(
            path=dataset_path,
            target=config.get("target_column"),
        )
        memory.dataset = dataset

    return memory


def update_project_config_from_memory(
    project_root: Path, memory: ProjectMemory
) -> None:
    """
    Sync memory back into the lightweight configuration file.
    """
    config = load_project_config(project_root) or {}
    config["project_name"] = memory.project_name
    config["project_goal"] = memory.project_goal
    config["current_stage"] = memory.current_stage
    config["completed_tasks"] = memory.completed_tasks
    config["notes"] = memory.notes

    if memory.dataset:
        config["dataset_path"] = str(memory.dataset.path)
        config["target_column"] = memory.dataset.target

    save_project_config(project_root, config)
