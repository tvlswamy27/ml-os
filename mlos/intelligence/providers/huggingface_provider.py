import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage


class HuggingFaceLocalProvider(IntelligenceProvider):
    """
    Local HuggingFace model provider using transformers pipeline.
    """

    def __init__(self, config: Any):
        super().__init__(config)
        self._pipeline = None

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            from transformers import pipeline  # type: ignore[import-not-found]

            self._pipeline = pipeline(
                "text-generation", model=self.config.model, device_map="auto"
            )
        return self._pipeline

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        start_time = datetime.utcnow()
        pipe = self._get_pipeline()

        prompt = f"<system>\n{system_prompt}\n</system>\n<user>\n{user_prompt}\n</user>\n<assistant>\n"

        res = pipe(
            prompt,
            max_new_tokens=self.config.max_tokens,
            temperature=(
                self.config.temperature if self.config.temperature > 0 else 0.01
            ),
            do_sample=self.config.temperature > 0,
        )
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        full_text = res[0]["generated_text"]
        content = full_text[len(prompt) :]

        input_tokens = len(prompt) // 4
        output_tokens = len(content) // 4
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="huggingface",
            model=self.config.model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=0.0,
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
            system_prompt + "\nOutput strictly valid JSON conforming to schema.",
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
