import os
from typing import Any

from mlos.intelligence.prompts.prompt_loader import ParsedPrompt, PromptLoader


class PromptManager:
    """
    Manages loading, caching, and formatting of subsystem prompts.
    """

    def __init__(self, base_dir: str = "mlos/prompts"):
        self.base_dir = base_dir
        self._cache: dict[str, ParsedPrompt] = {}

    def get_prompt(self, subsystem: str, prompt_name: str = "default") -> ParsedPrompt:
        """
        Retrieves a prompt from cache or loads it from disk.
        """
        key = f"{subsystem}/{prompt_name}"
        if key in self._cache:
            return self._cache[key]

        # Resolve path
        file_path = os.path.join(self.base_dir, subsystem, f"{prompt_name}.yaml")
        # Support fallback or default prompt if not found
        if not os.path.exists(file_path):
            file_path = os.path.join(
                self.base_dir, subsystem, f"default_{subsystem}.yaml"
            )
            # Try plain prompt_name.yaml or default if base directory fallback
            if not os.path.exists(file_path):
                file_path = os.path.join(
                    self.base_dir, subsystem, f"{prompt_name}.yaml"
                )

        parsed = PromptLoader.load_from_yaml(file_path)
        self._cache[key] = parsed
        return parsed

    def format_user_prompt(self, prompt: ParsedPrompt, **kwargs: Any) -> str:
        """
        Formats user prompt template with variable args.
        """
        import string

        formatter = string.Formatter()
        keys = [
            field_name
            for _, field_name, _, _ in formatter.parse(prompt.user_prompt_template)
            if field_name is not None
        ]
        for key in keys:
            if key not in kwargs:
                kwargs[key] = ""
        return prompt.user_prompt_template.format(**kwargs)
