import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Any


class LLMCache:
    """
    Semantic and cryptographic caching layer for LLM API transactions.
    """

    def __init__(self, cache_dir: str = ".gemini/cache", ttl_days: int = 7):
        self.cache_dir: str | None = cache_dir
        self.ttl_days = ttl_days
        self._memory_cache: dict[str, dict[str, Any]] = {}

        try:
            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            # Fallback to in-memory only if cannot create cache directory
            self.cache_dir = None

    def _generate_key(
        self,
        system_prompt: str,
        developer_prompt: str | None,
        user_prompt: str,
        response_schema: Any,
        provider_config: dict[str, Any],
    ) -> str:
        # Stringify response_schema
        schema_str = ""
        if response_schema is not None:
            if hasattr(response_schema, "model_json_schema"):
                try:
                    schema_str = json.dumps(
                        response_schema.model_json_schema(), sort_keys=True
                    )
                except Exception:
                    schema_str = str(response_schema)
            else:
                schema_str = str(response_schema)

        # Stringify provider_config
        config_str = json.dumps(provider_config, sort_keys=True)

        combined = (
            system_prompt
            + (developer_prompt or "")
            + user_prompt
            + schema_str
            + config_str
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def lookup(
        self,
        system_prompt: str,
        developer_prompt: str | None,
        user_prompt: str,
        response_schema: Any,
        provider_config: dict[str, Any],
    ) -> tuple[Any, bool]:
        """
        Check cache for matching query. Returns (cached_parsed_output, cache_hit).
        """
        key = self._generate_key(
            system_prompt,
            developer_prompt,
            user_prompt,
            response_schema,
            provider_config,
        )

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not self._is_expired(entry["timestamp"]):
                return entry["parsed_output"], True
            else:
                self.invalidate(key)

        # Check file cache
        if self.cache_dir:
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        entry = json.load(f)
                    if not self._is_expired(entry["timestamp"]):
                        # Store in memory for faster subsequent lookups
                        self._memory_cache[key] = entry
                        return entry["parsed_output"], True
                    else:
                        self.invalidate(key)
                except Exception:
                    pass

        return None, False

    def store(
        self,
        system_prompt: str,
        developer_prompt: str | None,
        user_prompt: str,
        response_schema: Any,
        provider_config: dict[str, Any],
        parsed_output: Any,
    ) -> None:
        """
        Store result in cache.
        """
        key = self._generate_key(
            system_prompt,
            developer_prompt,
            user_prompt,
            response_schema,
            provider_config,
        )

        serialized_output = parsed_output
        if parsed_output is not None:
            if hasattr(parsed_output, "model_dump"):
                serialized_output = parsed_output.model_dump()
            else:
                from dataclasses import asdict, is_dataclass

                if is_dataclass(parsed_output) and not isinstance(parsed_output, type):
                    serialized_output = asdict(parsed_output)

        entry = {
            "parsed_output": serialized_output,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store in memory
        self._memory_cache[key] = entry

        # Store in file
        if self.cache_dir:
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(entry, f, indent=2, sort_keys=True)
            except Exception:
                pass

    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache key.
        """
        self._memory_cache.pop(key, None)
        if self.cache_dir:
            file_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    def clear(self) -> None:
        """
        Clear all cache entries.
        """
        self._memory_cache.clear()
        if self.cache_dir and os.path.exists(self.cache_dir):
            for file_name in os.listdir(self.cache_dir):
                if file_name.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.cache_dir, file_name))
                    except Exception:
                        pass

    def _is_expired(self, timestamp_str: str) -> bool:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return datetime.utcnow() - timestamp > timedelta(days=self.ttl_days)
        except Exception:
            return True
