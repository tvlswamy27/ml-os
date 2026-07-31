from typing import Type
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.providers.openai_provider import OpenAIProvider
from mlos.intelligence.providers.anthropic_provider import AnthropicProvider
from mlos.intelligence.providers.gemini_provider import GeminiProvider
from mlos.intelligence.providers.ollama_provider import OllamaProvider
from mlos.intelligence.providers.huggingface_provider import HuggingFaceLocalProvider
from mlos.intelligence.providers.mock_provider import MockProvider


class ProviderFactory:
    """
    Factory for instantiating the requested IntelligenceProvider subclass from configuration.
    """

    _providers: dict[str, Type[IntelligenceProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
        "huggingface": HuggingFaceLocalProvider,
        "mock": MockProvider,
    }

    @classmethod
    def create_provider(cls, config: ProviderConfig) -> IntelligenceProvider:
        """
        Creates and returns the appropriate IntelligenceProvider.
        """
        provider_name = config.provider.lower()
        provider_class = cls._providers.get(provider_name)
        if provider_class is None:
            raise ValueError(f"Unknown or unsupported provider: {config.provider}")
        return provider_class(config)
