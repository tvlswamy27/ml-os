import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage


class GeminiProvider(IntelligenceProvider):
    """
    Gemini provider implementation.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        import google.generativeai as genai  # type: ignore[import-not-found]

        genai.configure(api_key=self.config.api_key or "dummy")
        start_time = datetime.utcnow()

        model = genai.GenerativeModel(
            model_name=self.config.model, system_instruction=system_prompt
        )

        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                candidate_count=1,
            ),
        )
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = response.text or ""

        # Estimate tokens
        input_tokens = len(user_prompt) // 4
        output_tokens = len(content) // 4
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )
        cost = (input_tokens * 0.075 / 1e6) + (output_tokens * 0.3 / 1e6)

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="gemini",
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
        import google.generativeai as genai  # type: ignore[import-not-found]

        genai.configure(api_key=self.config.api_key or "dummy")
        start_time = datetime.utcnow()

        model = genai.GenerativeModel(
            model_name=self.config.model, system_instruction=system_prompt
        )

        # Gemini supports structured outputs natively via response_mime_type and response_schema
        mime_type = "text/plain"
        schema_def = None
        if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
            mime_type = "application/json"
            schema_def = response_schema

        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                response_mime_type=mime_type,
                response_schema=schema_def,
                candidate_count=1,
            ),
        )
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = response.text or "{}"
        try:
            parsed = json.loads(content)
            if isinstance(response_schema, type) and issubclass(
                response_schema, BaseModel
            ):
                parsed = response_schema.model_validate(parsed)
        except Exception:
            parsed = None

        input_tokens = len(user_prompt) // 4
        output_tokens = len(content) // 4
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )
        cost = (input_tokens * 0.075 / 1e6) + (output_tokens * 0.3 / 1e6)

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="gemini",
            model=self.config.model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=cost,
            cache_hit=False,
            timestamp=end_time,
        )
        return parsed, metrics
