from abc import ABC, abstractmethod
from typing import Any
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema


class IntelligenceProvider(ABC):
    """
    Abstract Base Class for all LLM/SLM providers.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        """Generate free-form text response."""
        pass

    @abstractmethod
    def structured_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: StructuredOutputSchema,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[Any, CallMetrics]:
        """Generate structured data conforming to schema."""
        pass

    def embeddings(self, text: str) -> list[float]:
        """Future placeholder for generating vector embeddings."""
        raise NotImplementedError("Embeddings method is a future placeholder.")
