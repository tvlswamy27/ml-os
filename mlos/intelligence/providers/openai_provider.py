import json
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema


class OpenAIProvider(IntelligenceProvider):
    """
    OpenAI provider implementation.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        import openai  # type: ignore[import-not-found]

        client = openai.OpenAI(
            api_key=self.config.api_key or "sk-dummy",
            base_url=self.config.endpoint,
        )

        start_time = datetime.utcnow()
        messages = [{"role": "system", "content": system_prompt}]
        if developer_prompt:
            messages.insert(0, {"role": "developer", "content": developer_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            seed=self.config.seed,
            timeout=self.config.timeout,
        )

        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = response.choices[0].message.content or ""

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        token_usage = TokenUsage(input_tokens, output_tokens, total_tokens)

        cost = (input_tokens * 5.0 / 1e6) + (output_tokens * 15.0 / 1e6)

        metrics = CallMetrics(
            request_id=response.id,
            provider="openai",
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
        import openai  # type: ignore[import-not-found]

        client = openai.OpenAI(
            api_key=self.config.api_key or "sk-dummy",
            base_url=self.config.endpoint,
        )

        start_time = datetime.utcnow()
        messages = [{"role": "system", "content": system_prompt}]
        if developer_prompt:
            messages.insert(0, {"role": "developer", "content": developer_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # Check response_schema type
        if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
            response = client.beta.chat.completions.parse(
                model=self.config.model,
                messages=messages,
                response_format=response_schema,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed,
                timeout=self.config.timeout,
            )
            parsed_output = response.choices[0].message.parsed
        else:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed,
                timeout=self.config.timeout,
            )
            content = response.choices[0].message.content or "{}"
            parsed_output = json.loads(content)

        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        token_usage = TokenUsage(input_tokens, output_tokens, total_tokens)
        cost = (input_tokens * 5.0 / 1e6) + (output_tokens * 15.0 / 1e6)

        metrics = CallMetrics(
            request_id=response.id,
            provider="openai",
            model=self.config.model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=cost,
            cache_hit=False,
            timestamp=end_time,
        )
        return parsed_output, metrics
