from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: float = 10.0
    retry_limit: int = 3
    seed: int = 42
    endpoint: str | None = None
    api_key: str | None = None
