from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage


class MockProvider(IntelligenceProvider):
    """
    Deterministic Mock provider that requires no API keys and returns pre-defined frozen outputs.
    """

    mock_responses: dict[str, str] = {}
    mock_structured_responses: dict[Any, Any] = {}

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        # Check custom mock response register
        response_text = self.mock_responses.get(
            user_prompt, "Deterministic mock text response from MockProvider."
        )

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="mock",
            model=self.config.model,
            latency_ms=10.0,
            token_usage=TokenUsage(10, 20, 30),
            cost=0.0,
            cache_hit=False,
            timestamp=datetime.utcnow(),
        )
        return response_text, metrics

    def structured_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: StructuredOutputSchema,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[Any, CallMetrics]:
        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="mock",
            model=self.config.model,
            latency_ms=12.0,
            token_usage=TokenUsage(15, 25, 40),
            cost=0.0,
            cache_hit=False,
            timestamp=datetime.utcnow(),
        )

        # Check custom mock response register
        if response_schema in self.mock_structured_responses:
            return self.mock_structured_responses[response_schema], metrics

        # Fallback to generating default object for Pydantic models
        if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
            dummy_data: dict[str, Any] = {}
            for field_name, field_info in response_schema.model_fields.items():
                annotation = field_info.annotation
                if annotation == str:
                    dummy_data[field_name] = f"mock_{field_name}"
                elif annotation == int:
                    dummy_data[field_name] = 1
                elif annotation == float:
                    dummy_data[field_name] = 1.0
                elif annotation == bool:
                    dummy_data[field_name] = True
                elif annotation == list[str] or annotation == list:
                    dummy_data[field_name] = [f"mock_{field_name}_item"]
                elif annotation == dict[str, str] or annotation == dict:
                    dummy_data[field_name] = {"mock_key": "mock_value"}
                else:
                    dummy_data[field_name] = None
            try:
                obj = response_schema.model_validate(dummy_data)
                return obj, metrics
            except Exception:
                pass

        # Basic fallback instantiation
        try:
            return response_schema(), metrics  # type: ignore[operator]
        except Exception:
            return None, metrics
