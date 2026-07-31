import os
from dataclasses import dataclass
import yaml  # type: ignore[import-untyped]
from mlos.intelligence.prompts.prompt_version import PromptVersion


@dataclass(frozen=True)
class ParsedPrompt:
    version_info: PromptVersion
    system_prompt: str
    user_prompt_template: str
    developer_prompt: str | None = None


class PromptLoader:
    """
    Loads and parses YAML prompt configurations from disk.
    """

    @staticmethod
    def load_from_yaml(file_path: str) -> ParsedPrompt:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt file not found at {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        version_info = PromptVersion(
            version=str(data.get("version", "1.0.0")),
            author=str(data.get("author", "Unknown")),
            subsystem=str(data.get("subsystem", "general")),
            compatible_models=list(data.get("compatible_models", [])),
            changelog=list(data.get("changelog", [])),
        )

        return ParsedPrompt(
            version_info=version_info,
            system_prompt=str(data.get("system_prompt", "")),
            user_prompt_template=str(data.get("user_prompt_template", "")),
            developer_prompt=data.get("developer_prompt"),
        )
