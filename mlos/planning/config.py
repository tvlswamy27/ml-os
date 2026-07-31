"""
Planning configuration loading and AlgorithmMode definition.

Author: Vikram Tanakala
License: MIT
"""

from enum import Enum


class AlgorithmMode(Enum):
    """
    Enum representing the available planning algorithm modes.
    """

    RULE = "rule"
    LLM = "llm"
    HYBRID = "hybrid"


def get_planner_config() -> dict:
    """
    Load planning settings from the project's .mlos/project_config.yaml file.
    """
    from mlos.cli.persistence import find_project_root, load_project_config

    project_root = find_project_root()
    if project_root:
        config = load_project_config(project_root)
        if config and "planner" in config:
            return config["planner"]
    return {}
