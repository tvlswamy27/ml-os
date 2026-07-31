from datetime import datetime
import json
from typing import Any
from uuid import uuid4
import urllib.request
import urllib.error
from pydantic import BaseModel
from mlos.intelligence.providers.provider import IntelligenceProvider
from mlos.intelligence.telemetry.call_metrics import CallMetrics
from mlos.intelligence.telemetry.token_usage import TokenUsage
from mlos.intelligence.schemas.structured_output import StructuredOutputSchema


class OllamaProvider(IntelligenceProvider):
    """
    Ollama local provider implementation using HTTP requests.
    """

    def _call_http(self, path: str, payload: dict) -> dict:
        endpoint = self.config.endpoint or "http://localhost:11434"
        url = f"{endpoint.rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        developer_prompt: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, CallMetrics]:
        start_time = datetime.utcnow()

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "seed": self.config.seed,
            },
        }

        res = self._call_http("/api/chat", payload)
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = res.get("message", {}).get("content", "")

        input_tokens = res.get("prompt_eval_count", len(user_prompt) // 4)
        output_tokens = res.get("eval_count", len(content) // 4)
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="ollama",
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
        # Ollama supports structured JSON output format
        start_time = datetime.utcnow()

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "seed": self.config.seed,
            },
        }

        res = self._call_http("/api/chat", payload)
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000.0

        content = res.get("message", {}).get("content", "{}")
        try:
            parsed = json.loads(content)
            if isinstance(response_schema, type) and issubclass(
                response_schema, BaseModel
            ):
                parsed = response_schema.model_validate(parsed)
        except Exception:
            parsed = None

        input_tokens = res.get("prompt_eval_count", len(user_prompt) // 4)
        output_tokens = res.get("eval_count", len(content) // 4)
        token_usage = TokenUsage(
            input_tokens, output_tokens, input_tokens + output_tokens
        )

        metrics = CallMetrics(
            request_id=str(uuid4()),
            provider="ollama",
            model=self.config.model,
            latency_ms=latency_ms,
            token_usage=token_usage,
            cost=0.0,
            cache_hit=False,
            timestamp=end_time,
        )
        return parsed, metrics
