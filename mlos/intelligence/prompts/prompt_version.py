from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVersion:
    """
    Immutable representation of prompt metadata and changelog versioning.
    """

    version: str
    author: str
    subsystem: str
    compatible_models: list[str]
    changelog: list[str]
