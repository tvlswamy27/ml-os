import pytest
from pydantic import BaseModel, Field

from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.prompts.prompt_loader import PromptLoader
from mlos.intelligence.prompts.prompt_manager import PromptManager
from mlos.intelligence.provider_factory import ProviderFactory
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.schemas.llm_request import LLMRequest
from mlos.intelligence.validation.hybrid_validator import HybridValidator
from mlos.intelligence.validation.schema_validator import SchemaValidator


# Define a test Pydantic model for structured outputs
class DummyOutput(BaseModel):
    selected_imputer: str = Field(description="Mock imputer")
    confidence: float = Field(description="Mock confidence score")


def test_provider_config():
    config = ProviderConfig(
        provider="mock", model="mock-gpt", temperature=0.5, max_tokens=500
    )
    assert config.provider == "mock"
    assert config.model == "mock-gpt"
    assert config.temperature == 0.5
    assert config.max_tokens == 500


def test_provider_factory():
    config = ProviderConfig(provider="mock", model="mock-gpt")
    provider = ProviderFactory.create_provider(config)
    assert isinstance(provider, MockProvider)

    with pytest.raises(ValueError):
        invalid_config = ProviderConfig(provider="nonexistent", model="none")
        ProviderFactory.create_provider(invalid_config)


def test_mock_provider_generation():
    config = ProviderConfig(provider="mock", model="mock-gpt")
    provider = ProviderFactory.create_provider(config)

    # Text generate
    response, metrics = provider.generate("System instruction", "User query")
    assert "mock" in response.lower()
    assert metrics.provider == "mock"
    assert metrics.token_usage.total_tokens == 30

    # Structured generate (fallback instantiation)
    obj, metrics = provider.structured_generate("System", "Query", DummyOutput)
    assert isinstance(obj, DummyOutput)
    assert obj.selected_imputer == "mock_selected_imputer"
    assert obj.confidence == 1.0


def test_prompt_loader_and_manager():
    # Prompt Loader
    file_path = "mlos/prompts/planning/default_planning.yaml"
    parsed = PromptLoader.load_from_yaml(file_path)
    assert parsed.version_info.subsystem == "planning"
    assert parsed.system_prompt == "You are the Planning Intelligence Subsystem."

    # Prompt Manager
    manager = PromptManager(base_dir="mlos/prompts")
    prompt = manager.get_prompt("planning", "default_planning")
    assert prompt.version_info.version == "1.0.0"

    formatted = manager.format_user_prompt(
        prompt, project_name="TestProj", goals="Regression"
    )
    assert formatted == "Project: TestProj, Goals: Regression"


def test_llm_cache():
    cache = LLMCache(cache_dir=".gemini/test_cache")
    cache.clear()

    system_prompt = "Sys"
    developer_prompt = "Dev"
    user_prompt = "User"
    schema = DummyOutput
    config_dict = {"provider": "mock", "model": "gpt"}

    output, hit = cache.lookup(
        system_prompt, developer_prompt, user_prompt, schema, config_dict
    )
    assert not hit

    dummy_obj = {"selected_imputer": "mean", "confidence": 0.9}
    cache.store(
        system_prompt, developer_prompt, user_prompt, schema, config_dict, dummy_obj
    )

    # Lookup should now hit
    output, hit = cache.lookup(
        system_prompt, developer_prompt, user_prompt, schema, config_dict
    )
    assert hit
    assert output == dummy_obj

    cache.clear()
    output, hit = cache.lookup(
        system_prompt, developer_prompt, user_prompt, schema, config_dict
    )
    assert not hit


def test_schema_validator():
    raw_valid_json = '{"selected_imputer": "median", "confidence": 0.85}'
    parsed, passed = SchemaValidator.validate_and_parse(raw_valid_json, DummyOutput)
    assert passed
    assert isinstance(parsed, DummyOutput)
    assert parsed.selected_imputer == "median"
    assert parsed.confidence == 0.85

    raw_invalid_json = '{"selected_imputer": "median"}'  # missing confidence
    parsed, passed = SchemaValidator.validate_and_parse(raw_invalid_json, DummyOutput)
    assert not passed


def test_hybrid_validator():
    def constraint_checker(output):
        return output.confidence >= 0.8

    valid_output = DummyOutput(selected_imputer="mean", confidence=0.9)
    result, passed = HybridValidator.validate_constraints(
        valid_output, constraint_checker, fallback_value="fallback"
    )
    assert passed
    assert result == valid_output

    invalid_output = DummyOutput(selected_imputer="mean", confidence=0.7)
    result, passed = HybridValidator.validate_constraints(
        invalid_output, constraint_checker, fallback_value="fallback"
    )
    assert not passed
    assert result == "fallback"


def test_intelligence_service_flow():
    config = ProviderConfig(provider="mock", model="mock-gpt")
    test_cache = LLMCache(cache_dir=".gemini/test_cache_service")
    test_cache.clear()
    service = IntelligenceService(default_config=config, cache=test_cache)

    request = LLMRequest(
        system_prompt="Sys", user_prompt="User", response_schema=DummyOutput
    )

    response = service.execute(request)
    assert response.validation_passed
    assert not response.cache_hit
    assert isinstance(response.parsed_output, DummyOutput)

    # Run again: should trigger cache hit
    response_cached = service.execute(request)
    assert response_cached.cache_hit
    assert response_cached.validation_passed
    assert response_cached.parsed_output == response.parsed_output
