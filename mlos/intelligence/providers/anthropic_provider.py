import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage


class AnthropicProvider(IntelligenceProvider):
    """
    Anthropic provider implementation.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        import anthropic  # type: ignore[import-not-found]

        client = anthropic.Anthropic(api_key=self.config.api_key or "dummy")
        start_time = datetime.utcnow()

        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=self.config.timeout,
        )
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = response.content[0].text if response.content else ""

        usage = response.usage
        input_tokens = usage.input_tokens if usage else 0
        output_tokens = usage.output_tokens if usage else 0
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )
        cost = (input_tokens * 3.0 / 1e6) + (output_tokens * 15.0 / 1e6)

        metrics = CallMetrics(
            request_id=response.id,
            provider="anthropic",
            model=self.config.model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=cost,
            cache_hit=False,
            timestamp=end_time,
        )
        return content, metrics

    def structured_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: StructuredOutputSchema,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[Any, CallMetrics]:
        content, metrics = self.generate(
            system_prompt
            + "\nRespond ONLY with a valid JSON object matching the requested schema.",
            user_prompt,
            developer_prompt,
            **kwargs,
        )
        try:
            parsed = json.loads(content)
            if isinstance(response_schema, type) and issubclass(
                response_schema, BaseModel
            ):
                parsed = response_schema.model_validate(parsed)
            return parsed, metrics
        except Exception:
            return None, metrics
