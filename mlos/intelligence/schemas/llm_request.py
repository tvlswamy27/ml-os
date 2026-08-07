from dataclasses import dataclass, field
from typing import Any

from mlos.intelligence.schemas.structured_output import StructuredOutputSchema


@dataclass(frozen=True)
class LLMRequest:
    """
    Strongly typed immutable request payload for an intelligence provider call.
    """

    system_prompt: str
    user_prompt: str
    developer_prompt: str | None = None
    response_schema: StructuredOutputSchema | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
